"""
Zero-dependency HTTP REST API and Static File Server for the ATM Management System.
Uses Python's built-in http.server and connects directly to storage.py.
"""
import os
import sys
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Add current directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import (
    ATM_NOTE_DENOMINATION,
    MIN_DEPOSIT_AMOUNT,
    PIN_LENGTH,
    MAX_LOGIN_ATTEMPTS
)
from storage import JSONStorage, SQLiteStorage
from utils import format_currency, mask_account_number, mask_phone
from transaction import (
    generate_transaction_id,
    create_transaction,
    get_current_datetime
)

# Persistent storage engine
storage = JSONStorage()

# Failed login attempt tracker per user_id: { user_id: attempts_failed }
login_attempts = {}


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handles HTTP requests asynchronously in separate threads."""
    daemon_threads = True
    allow_reuse_address = True


class ATMRequestHandler(BaseHTTPRequestHandler):
    """Custom request handler serving both REST API endpoints and static web assets."""

    def log_message(self, format, *args):
        """Clean custom logging for server requests."""
        sys.stdout.write(f"[{get_current_datetime()}] {args[0]} {args[1]} -> {args[2]}\n")

    def _send_json(self, status_code, payload):
        """Utility to send JSON response with CORS headers."""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        """Handles CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json_body(self):
        """Reads and parses incoming JSON payload from request body."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode("utf-8")
                return json.loads(body)
        except Exception:
            pass
        return {}

    def do_GET(self):
        """Handles GET requests: API data queries and static web assets."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # REST API Routes
        if path == "/api/sample-users":
            # Return public details of seed users for easy demo selection
            all_users = storage.load_data()
            sample_list = []
            for uid, udata in all_users.items():
                sample_list.append({
                    "user_id": uid,
                    "username": udata.get("username", "Customer"),
                    "masked_acc": mask_account_number(udata.get("acc_no", "")),
                    "phone": mask_phone(udata.get("phone", ""))
                })
            return self._send_json(200, {"users": sample_list})

        elif path.startswith("/api/user/"):
            uid = path.replace("/api/user/", "").strip().upper()
            user = storage.get_user(uid)
            if not user:
                return self._send_json(404, {"error": "User not found"})
            
            # Format user view without exposing PIN
            sanitized = {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "phone": mask_phone(user.get("phone", "")),
                "acc_no": mask_account_number(user.get("acc_no", "")),
                "avl_bal": float(user.get("avl_bal", 0.0)),
                "formatted_bal": format_currency(user.get("avl_bal", 0.0)),
                "history": user.get("history", {"withdraw_history": [], "deposit_history": []})
            }
            return self._send_json(200, {"user": sanitized})

        # Static Asset Serving
        if path == "/" or path == "/index.html":
            file_path = os.path.join(CURRENT_DIR, "static", "index.html")
        else:
            rel_path = path.lstrip("/")
            if rel_path.startswith("static/"):
                rel_path = rel_path.replace("static/", "", 1)
            file_path = os.path.join(CURRENT_DIR, "static", rel_path)

        if os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "text/plain"
            if mime_type.startswith("text/") or mime_type in ["application/javascript", "application/json"]:
                mime_type += "; charset=utf-8"

            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except OSError:
                self.send_error(500, "File read error")
                return

        self.send_error(404, "File Not Found")

    def do_POST(self):
        """Handles POST requests: Authentication and Transactions."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        body = self._read_json_body()

        # Route: Authentication
        if path == "/api/login":
            user_id = str(body.get("user_id", "")).strip().upper()
            pin = str(body.get("pin", "")).strip()

            if not user_id or not pin:
                return self._send_json(400, {"error": "User ID and PIN are required."})

            attempts = login_attempts.get(user_id, 0)
            if attempts >= MAX_LOGIN_ATTEMPTS:
                return self._send_json(403, {
                    "error": "Account session locked! Maximum 3 login attempts exceeded. Please contact bank administrator.",
                    "locked": True
                })

            all_users = storage.load_data()
            if user_id in all_users:
                user_data = all_users[user_id]
                if str(user_data.get("pin")) == pin:
                    # Reset failed attempts
                    login_attempts[user_id] = 0
                    sanitized_user = {
                        "user_id": user_id,
                        "username": user_data.get("username"),
                        "phone": mask_phone(user_data.get("phone", "")),
                        "acc_no": mask_account_number(user_data.get("acc_no", "")),
                        "avl_bal": float(user_data.get("avl_bal", 0.0)),
                        "formatted_bal": format_currency(user_data.get("avl_bal", 0.0)),
                        "history": user_data.get("history", {"withdraw_history": [], "deposit_history": []})
                    }
                    return self._send_json(200, {
                        "success": True,
                        "message": f"Welcome, {user_data.get('username')}!",
                        "user": sanitized_user
                    })

            # Record failed attempt
            login_attempts[user_id] = attempts + 1
            remaining = MAX_LOGIN_ATTEMPTS - login_attempts[user_id]
            if remaining <= 0:
                return self._send_json(403, {
                    "error": "Maximum 3 login attempts exceeded! Your session is now locked.",
                    "locked": True
                })
            return self._send_json(401, {
                "error": f"Invalid User ID or PIN. {remaining} attempt(s) remaining.",
                "remaining_attempts": remaining
            })

        # Route: Withdraw Cash
        elif path == "/api/withdraw":
            user_id = str(body.get("user_id", "")).strip().upper()
            try:
                amount = int(body.get("amount", 0))
            except (ValueError, TypeError):
                return self._send_json(400, {"error": "Invalid withdrawal amount."})

            user = storage.get_user(user_id)
            if not user:
                return self._send_json(404, {"error": "User session invalid. Please log in again."})

            if amount <= 0:
                return self._send_json(400, {"error": "Withdrawal amount must be greater than zero."})

            current_bal = float(user.get("avl_bal", 0.0))
            if amount > current_bal:
                return self._send_json(400, {
                    "error": f"Insufficient balance. Your balance is {format_currency(current_bal)}."
                })

            if amount % ATM_NOTE_DENOMINATION != 0:
                return self._send_json(400, {
                    "error": f"ATM only dispenses {format_currency(ATM_NOTE_DENOMINATION)} notes. Amount must be a multiple of {format_currency(ATM_NOTE_DENOMINATION)}."
                })

            # Process withdrawal
            user["avl_bal"] = current_bal - amount
            all_data = storage.load_data()
            txn_id = generate_transaction_id(all_data)
            txn = create_transaction(txn_id, "Withdraw", amount, user["avl_bal"])

            user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
            user["history"].setdefault("withdraw_history", []).append(txn)
            storage.save_user(user_id, user)

            num_notes = amount // ATM_NOTE_DENOMINATION

            return self._send_json(200, {
                "success": True,
                "message": f"Successfully withdrawn {format_currency(amount)}.",
                "notes_dispensed": num_notes,
                "note_denomination": ATM_NOTE_DENOMINATION,
                "transaction": txn,
                "new_balance": user["avl_bal"],
                "formatted_balance": format_currency(user["avl_bal"]),
                "history": user["history"]
            })

        # Route: Deposit Cash
        elif path == "/api/deposit":
            user_id = str(body.get("user_id", "")).strip().upper()
            try:
                amount = int(body.get("amount", 0))
            except (ValueError, TypeError):
                return self._send_json(400, {"error": "Invalid deposit amount."})

            user = storage.get_user(user_id)
            if not user:
                return self._send_json(404, {"error": "User session invalid."})

            if amount <= MIN_DEPOSIT_AMOUNT:
                return self._send_json(400, {
                    "error": f"Deposit amount must be strictly greater than {format_currency(MIN_DEPOSIT_AMOUNT)}."
                })

            if amount % ATM_NOTE_DENOMINATION != 0:
                return self._send_json(400, {
                    "error": f"Only {format_currency(ATM_NOTE_DENOMINATION)} notes are accepted. Amount must be in multiples of {format_currency(ATM_NOTE_DENOMINATION)}."
                })

            # Process deposit
            current_bal = float(user.get("avl_bal", 0.0))
            user["avl_bal"] = current_bal + amount
            all_data = storage.load_data()
            txn_id = generate_transaction_id(all_data)
            txn = create_transaction(txn_id, "Deposit", amount, user["avl_bal"])

            user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
            user["history"].setdefault("deposit_history", []).append(txn)
            storage.save_user(user_id, user)

            return self._send_json(200, {
                "success": True,
                "message": f"Successfully deposited {format_currency(amount)}.",
                "transaction": txn,
                "new_balance": user["avl_bal"],
                "formatted_balance": format_currency(user["avl_bal"]),
                "history": user["history"]
            })

        # Route: Change PIN
        elif path == "/api/change-pin":
            user_id = str(body.get("user_id", "")).strip().upper()
            current_pin = str(body.get("current_pin", "")).strip()
            new_pin = str(body.get("new_pin", "")).strip()
            confirm_pin = str(body.get("confirm_pin", "")).strip()

            user = storage.get_user(user_id)
            if not user:
                return self._send_json(404, {"error": "User session invalid."})

            if current_pin != str(user.get("pin")):
                return self._send_json(400, {"error": "Current PIN does not match."})

            if len(new_pin) != PIN_LENGTH or not new_pin.isdigit():
                return self._send_json(400, {"error": f"New PIN must contain exactly {PIN_LENGTH} digits."})

            if new_pin == str(user.get("pin")):
                return self._send_json(400, {"error": "New PIN cannot be identical to the old PIN."})

            if new_pin != confirm_pin:
                return self._send_json(400, {"error": "New PIN and confirmation PIN do not match."})

            user["pin"] = new_pin
            storage.save_user(user_id, user)
            return self._send_json(200, {"success": True, "message": "PIN updated successfully."})

        # Route: Register New User
        elif path == "/api/register":
            username = str(body.get("username", "")).strip()
            phone = str(body.get("phone", "")).strip()
            acc_no = str(body.get("acc_no", "")).strip()
            pin = str(body.get("pin", "")).strip()
            user_id = str(body.get("user_id", "")).strip().upper()
            try:
                init_bal = float(body.get("initial_balance", 0.0))
            except (ValueError, TypeError):
                return self._send_json(400, {"error": "Initial balance must be a valid number."})

            if not username or not phone or not acc_no or not pin or not user_id:
                return self._send_json(400, {"error": "All fields are required."})

            if not phone.isdigit():
                return self._send_json(400, {"error": "Phone number must contain only numeric digits."})

            if not acc_no.isdigit():
                return self._send_json(400, {"error": "Account number must contain only numeric digits."})

            if len(pin) != PIN_LENGTH or not pin.isdigit():
                return self._send_json(400, {"error": f"PIN must contain exactly {PIN_LENGTH} numeric digits."})

            if init_bal < 0:
                return self._send_json(400, {"error": "Initial balance cannot be negative."})

            all_users = storage.load_data()
            if user_id in all_users:
                return self._send_json(400, {"error": f"User ID '{user_id}' already exists."})

            if any(u.get("acc_no") == acc_no for u in all_users.values()):
                return self._send_json(400, {"error": "Account number is already registered."})

            new_record = {
                "username": username,
                "phone": phone,
                "acc_no": acc_no,
                "pin": pin,
                "user_id": user_id,
                "avl_bal": float(init_bal),
                "history": {
                    "withdraw_history": [],
                    "deposit_history": []
                }
            }
            storage.save_user(user_id, new_record)
            return self._send_json(201, {
                "success": True,
                "message": f"User {username} registered successfully with ID {user_id}!",
                "user_id": user_id
            })

        # Route: Clear History
        elif path == "/api/clear-history":
            user_id = str(body.get("user_id", "")).strip().upper()
            clear_type = str(body.get("type", "all")).strip().lower()

            user = storage.get_user(user_id)
            if not user:
                return self._send_json(404, {"error": "User session invalid."})

            history = user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
            if clear_type == "withdraw":
                history["withdraw_history"] = []
                msg = "Withdrawal history cleared."
            elif clear_type == "deposit":
                history["deposit_history"] = []
                msg = "Deposit history cleared."
            else:
                history["withdraw_history"] = []
                history["deposit_history"] = []
                msg = "All transaction history cleared."

            storage.save_user(user_id, user)
            return self._send_json(200, {"success": True, "message": msg, "history": history})

        self.send_error(404, "Endpoint not found")


def start_server(port=8080):
    """Starts the threaded HTTP server."""
    server_address = ("127.0.0.1", port)
    httpd = ThreadedHTTPServer(server_address, ATMRequestHandler)
    print(f"\n" + "=" * 50)
    print(f" 🏧 ATM Web Frontend Server Running!")
    print(f" Access URL: http://127.0.0.1:{port}")
    print(f" Press Ctrl+C to stop the server.")
    print("=" * 50 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ATM Web Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port)
