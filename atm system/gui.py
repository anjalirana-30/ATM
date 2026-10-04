"""
Standalone Native Desktop GUI for the ATM Banking Management System.
Built with Python's standard library tkinter (zero extra pip packages required).
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure current directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import (
    ATM_NOTE_DENOMINATION,
    MIN_DEPOSIT_AMOUNT,
    MAX_LOGIN_ATTEMPTS,
    QUICK_WITHDRAW_OPTIONS,
    PIN_LENGTH
)
from storage import JSONStorage
from utils import format_currency, mask_account_number, mask_phone
from transaction import generate_transaction_id, create_transaction, get_current_datetime

# Color Palette
BG_DARK = "#0f172a"
CARD_BG = "#1e293b"
ACCENT_GREEN = "#10b981"
ACCENT_BLUE = "#3b82f6"
TEXT_WHITE = "#f8fafc"
TEXT_MUTED = "#94a3b8"
DANGER_RED = "#ef4444"


class ATMGuiApp(tk.Tk):
    """Main Desktop GUI Window for the ATM Management System."""

    def __init__(self):
        super().__init__()
        self.title("🏧 ATM Banking Management System")
        self.geometry("720x680")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        # Storage & Session State
        self.storage = JSONStorage()
        self.current_user = None
        self.failed_attempts = 0

        # Container for swappable screens
        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        self.create_views()
        self.show_view("LoginView")

    def create_views(self):
        """Initializes all ATM application screen frames."""
        for ViewClass in (
            LoginView,
            DashboardView,
            WithdrawView,
            DepositView,
            QuickWithdrawView,
            StatementView,
            AccountDetailsView,
            ChangePinView,
            RegisterView
        ):
            name = ViewClass.__name__
            frame = ViewClass(parent=self.container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, view_name):
        """Switches the active screen."""
        frame = self.frames[view_name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def login_user(self, user_id, pin):
        """Authenticates user with 3-attempt limit."""
        if self.failed_attempts >= MAX_LOGIN_ATTEMPTS:
            messagebox.showerror("Session Locked", "Maximum login attempts exceeded. Session is locked!")
            return False

        all_users = self.storage.load_data()
        user_id = user_id.strip().upper()

        if user_id in all_users:
            udata = all_users[user_id]
            if str(udata.get("pin")) == str(pin).strip():
                self.current_user = udata
                self.failed_attempts = 0
                self.show_view("DashboardView")
                return True

        self.failed_attempts += 1
        rem = MAX_LOGIN_ATTEMPTS - self.failed_attempts
        if rem <= 0:
            messagebox.showerror("Session Locked", "3 failed attempts. Session locked!")
        else:
            messagebox.showwarning("Login Failed", f"Invalid User ID or PIN!\n{rem} attempt(s) remaining.")
        return False

    def logout_user(self):
        """Logs out the active user and returns to login view."""
        self.current_user = None
        self.show_view("LoginView")


class BaseView(tk.Frame):
    """Base class for all screen frames with uniform styling."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller = controller

    def create_header(self, title_text):
        """Helper to create a standard header."""
        header = tk.Frame(self, bg=CARD_BG, pady=14, padx=20)
        header.pack(fill="x", pady=(0, 20))
        lbl = tk.Label(header, text=title_text, font=("Segoe UI", 16, "bold"), fg=TEXT_WHITE, bg=CARD_BG)
        lbl.pack(side="left")
        return header


class LoginView(BaseView):
    """ATM Authentication Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("🏧 METRO APEX BANK — ATM LOGIN")

        card = tk.Frame(self, bg=CARD_BG, padx=30, pady=30)
        card.pack(pady=40)

        tk.Label(card, text="Insert Card / Enter Credentials", font=("Segoe UI", 13, "bold"), fg=TEXT_WHITE, bg=CARD_BG).pack(pady=(0, 16))

        tk.Label(card, text="User ID (e.g. A111):", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.uid_entry = tk.Entry(card, font=("Segoe UI", 14), width=24, justify="center")
        self.uid_entry.pack(pady=(4, 14))

        tk.Label(card, text="4-Digit PIN:", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.pin_entry = tk.Entry(card, font=("Segoe UI", 14), show="*", width=24, justify="center")
        self.pin_entry.pack(pady=(4, 20))

        btn_login = tk.Button(card, text="✔ Login to ATM", font=("Segoe UI", 12, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
                              activebackground="#059669", cursor="hand2", padx=20, pady=8, command=self.do_login)
        btn_login.pack(fill="x", pady=6)

        btn_reg = tk.Button(card, text="➕ Register New User", font=("Segoe UI", 10), bg=CARD_BG, fg=ACCENT_BLUE,
                            bd=0, cursor="hand2", command=lambda: controller.show_view("RegisterView"))
        btn_reg.pack(pady=10)

        # Quick account picker buttons
        pills_frame = tk.Frame(self, bg=BG_DARK)
        pills_frame.pack(pady=10)
        tk.Label(pills_frame, text="Quick Demo Accounts:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_DARK).pack(pady=4)

        btn_bar = tk.Frame(pills_frame, bg=BG_DARK)
        btn_bar.pack()
        for uid, pin, name in [("A111", "1414", "Anjali"), ("H112", "2563", "Honey"), ("H113", "4785", "Harsh"), ("K114", "0125", "Keval")]:
            b = tk.Button(btn_bar, text=f"{name} ({uid})", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_WHITE,
                          padx=8, pady=4, cursor="hand2", command=lambda u=uid, p=pin: self.fill_and_login(u, p))
            b.pack(side="left", padx=4)

    def fill_and_login(self, uid, pin):
        self.uid_entry.delete(0, tk.END)
        self.uid_entry.insert(0, uid)
        self.pin_entry.delete(0, tk.END)
        self.pin_entry.insert(0, pin)
        self.do_login()

    def do_login(self):
        uid = self.uid_entry.get()
        pin = self.pin_entry.get()
        if not uid or not pin:
            messagebox.showwarning("Incomplete", "Please enter both User ID and PIN.")
            return
        if self.controller.login_user(uid, pin):
            self.pin_entry.delete(0, tk.END)


class DashboardView(BaseView):
    """Main ATM Operations Dashboard."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.header = self.create_header("🏧 ATM DASHBOARD")

        # Balance Card
        self.bal_card = tk.Frame(self, bg=CARD_BG, padx=24, pady=18)
        self.bal_card.pack(fill="x", padx=30, pady=(0, 16))

        self.welcome_lbl = tk.Label(self.bal_card, text="Welcome, Customer 👋", font=("Segoe UI", 14, "bold"), fg=TEXT_WHITE, bg=CARD_BG)
        self.welcome_lbl.pack(anchor="w")

        self.acc_lbl = tk.Label(self.bal_card, text="Account: ******452452", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG)
        self.acc_lbl.pack(anchor="w", pady=(2, 8))

        tk.Label(self.bal_card, text="AVAILABLE BALANCE", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.bal_val_lbl = tk.Label(self.bal_card, text="₹10,000", font=("Segoe UI", 26, "bold"), fg=ACCENT_GREEN, bg=CARD_BG)
        self.bal_val_lbl.pack(anchor="w")

        # Grid of Actions
        grid_frame = tk.Frame(self, bg=BG_DARK)
        grid_frame.pack(fill="both", expand=True, padx=30, pady=10)

        actions = [
            ("💰 Withdraw Cash", "WithdrawView", ACCENT_BLUE),
            ("💵 Deposit Cash", "DepositView", ACCENT_GREEN),
            ("⚡ Quick Withdraw", "QuickWithdrawView", "#f59e0b"),
            ("📄 Mini Statement", "StatementView", "#8b5cf6"),
            ("👤 Account Details", "AccountDetailsView", "#06b6d4"),
            ("🔑 Change PIN", "ChangePinView", "#ec4899"),
            ("➕ Register User", "RegisterView", "#64748b"),
            ("🚪 Logout", "logout", DANGER_RED)
        ]

        for i, (text, route, color) in enumerate(actions):
            r, c = divmod(i, 2)
            btn = tk.Button(grid_frame, text=text, font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=color,
                            activebackground=color, activeforeground=BG_DARK, bd=1, relief="solid",
                            padx=14, pady=14, cursor="hand2",
                            command=lambda rt=route: self.on_action_click(rt))
            btn.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            grid_frame.grid_columnconfigure(c, weight=1)
            grid_frame.grid_rowconfigure(r, weight=1)

    def on_show(self):
        user = self.controller.current_user
        if user:
            self.welcome_lbl.config(text=f"Welcome, {user.get('username')} 👋")
            self.acc_lbl.config(text=f"Account: {mask_account_number(user.get('acc_no'))}")
            self.bal_val_lbl.config(text=format_currency(user.get("avl_bal", 0.0)))

    def on_action_click(self, route):
        if route == "logout":
            self.controller.logout_user()
        else:
            self.controller.show_view(route)


class WithdrawView(BaseView):
    """Cash Withdrawal Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("💰 CASH WITHDRAWAL")

        card = tk.Frame(self, bg=CARD_BG, padx=30, pady=30)
        card.pack(pady=30)

        tk.Label(card, text="ATM dispenses ₹500 notes only", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(pady=(0, 14))

        tk.Label(card, text="Enter Amount (₹):", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=CARD_BG).pack(anchor="w")
        self.amt_entry = tk.Entry(card, font=("Segoe UI", 16, "bold"), justify="center", width=18)
        self.amt_entry.pack(pady=(6, 20))

        tk.Button(card, text="Dispense Cash 💵", font=("Segoe UI", 12, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
                  padx=20, pady=10, cursor="hand2", command=self.do_withdraw).pack(fill="x", pady=6)

        tk.Button(card, text="Cancel", font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_MUTED,
                  command=lambda: controller.show_view("DashboardView")).pack(fill="x", pady=4)

    def do_withdraw(self):
        user = self.controller.current_user
        try:
            amt = int(self.amt_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid whole number.")
            return

        if amt <= 0:
            messagebox.showerror("Error", "Amount must be greater than zero.")
            return

        if amt > user["avl_bal"]:
            messagebox.showerror("Insufficient Balance", f"Your balance is only {format_currency(user['avl_bal'])}.")
            return

        if amt % ATM_NOTE_DENOMINATION != 0:
            messagebox.showerror("Denomination Error", f"ATM only dispenses {format_currency(ATM_NOTE_DENOMINATION)} notes.")
            return

        # Deduct balance & record transaction
        user["avl_bal"] -= amt
        all_data = self.controller.storage.load_data()
        txn_id = generate_transaction_id(all_data)
        txn = create_transaction(txn_id, "Withdraw", amt, user["avl_bal"])

        user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
        user["history"].setdefault("withdraw_history", []).append(txn)
        self.controller.storage.save_user(user["user_id"], user)

        messagebox.showinfo("Success", f"✔ Successfully withdrawn {format_currency(amt)}!\nTransaction ID: {txn_id}\nRemaining Balance: {format_currency(user['avl_bal'])}")
        self.amt_entry.delete(0, tk.END)
        self.controller.show_view("DashboardView")


class DepositView(BaseView):
    """Cash Deposit Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("💵 CASH DEPOSIT")

        card = tk.Frame(self, bg=CARD_BG, padx=30, pady=30)
        card.pack(pady=30)

        rules = f"• Deposit amount must be > {format_currency(MIN_DEPOSIT_AMOUNT)}\n• Multiples of {format_currency(ATM_NOTE_DENOMINATION)} notes only"
        tk.Label(card, text=rules, font=("Segoe UI", 10), justify="left", fg=TEXT_MUTED, bg=CARD_BG).pack(pady=(0, 16))

        tk.Label(card, text="Deposit Amount (₹):", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=CARD_BG).pack(anchor="w")
        self.amt_entry = tk.Entry(card, font=("Segoe UI", 16, "bold"), justify="center", width=18)
        self.amt_entry.pack(pady=(6, 20))

        tk.Button(card, text="Deposit Money 📥", font=("Segoe UI", 12, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
                  padx=20, pady=10, cursor="hand2", command=self.do_deposit).pack(fill="x", pady=6)

        tk.Button(card, text="Cancel", font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_MUTED,
                  command=lambda: controller.show_view("DashboardView")).pack(fill="x", pady=4)

    def do_deposit(self):
        user = self.controller.current_user
        try:
            amt = int(self.amt_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")
            return

        if amt <= MIN_DEPOSIT_AMOUNT:
            messagebox.showerror("Deposit Rule", f"Deposit amount must be strictly greater than {format_currency(MIN_DEPOSIT_AMOUNT)}.")
            return

        if amt % ATM_NOTE_DENOMINATION != 0:
            messagebox.showerror("Denomination Error", f"Only {format_currency(ATM_NOTE_DENOMINATION)} notes are accepted.")
            return

        # Credit balance & record transaction
        user["avl_bal"] += amt
        all_data = self.controller.storage.load_data()
        txn_id = generate_transaction_id(all_data)
        txn = create_transaction(txn_id, "Deposit", amt, user["avl_bal"])

        user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
        user["history"].setdefault("deposit_history", []).append(txn)
        self.controller.storage.save_user(user["user_id"], user)

        messagebox.showinfo("Success", f"✔ Successfully deposited {format_currency(amt)}!\nTransaction ID: {txn_id}\nNew Balance: {format_currency(user['avl_bal'])}")
        self.amt_entry.delete(0, tk.END)
        self.controller.show_view("DashboardView")


class QuickWithdrawView(BaseView):
    """Preset Quick Cash Shortcuts."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("⚡ QUICK WITHDRAW")

        grid = tk.Frame(self, bg=BG_DARK)
        grid.pack(pady=30, padx=40)

        for i, amt in enumerate(QUICK_WITHDRAW_OPTIONS):
            r, c = divmod(i, 2)
            btn = tk.Button(grid, text=format_currency(amt), font=("Segoe UI", 14, "bold"),
                            bg=CARD_BG, fg=ACCENT_GREEN, width=14, pady=16, cursor="hand2",
                            command=lambda a=amt: self.do_quick_withdraw(a))
            btn.grid(row=r, column=c, padx=12, pady=12)

        tk.Button(self, text="Cancel", font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_MUTED,
                  command=lambda: controller.show_view("DashboardView")).pack(pady=10)

    def do_quick_withdraw(self, amt):
        user = self.controller.current_user
        if amt > user["avl_bal"]:
            messagebox.showerror("Insufficient Balance", f"Selected {format_currency(amt)}, but your balance is only {format_currency(user['avl_bal'])}.")
            return

        user["avl_bal"] -= amt
        all_data = self.controller.storage.load_data()
        txn_id = generate_transaction_id(all_data)
        txn = create_transaction(txn_id, "Withdraw", amt, user["avl_bal"])

        user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
        user["history"].setdefault("withdraw_history", []).append(txn)
        self.controller.storage.save_user(user["user_id"], user)

        messagebox.showinfo("Success", f"✔ Dispensed {format_currency(amt)}!\nTransaction ID: {txn_id}\nRemaining Balance: {format_currency(user['avl_bal'])}")
        self.controller.show_view("DashboardView")


class StatementView(BaseView):
    """Combined Mini Statement Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("📄 MINI STATEMENT")

        tree_frame = tk.Frame(self, bg=BG_DARK)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("date_time", "type", "amount", "balance")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        self.tree.heading("date_time", text="Date & Time")
        self.tree.heading("type", text="Type")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("balance", text="Balance")

        self.tree.column("date_time", width=160)
        self.tree.column("type", width=100)
        self.tree.column("amount", width=120)
        self.tree.column("balance", width=120)
        self.tree.pack(fill="both", expand=True)

        tk.Button(self, text="Back to Dashboard", font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_WHITE,
                  command=lambda: controller.show_view("DashboardView")).pack(pady=14)

    def on_show(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        user = self.controller.current_user
        if not user:
            return

        history = user.get("history", {})
        txns = []
        for t in history.get("withdraw_history", []):
            txns.append({**t, "type": "Withdraw"})
        for t in history.get("deposit_history", []):
            txns.append({**t, "type": "Deposit"})

        txns.sort(key=lambda x: x.get("date_time", ""), reverse=True)

        for t in txns:
            self.tree.insert("", "end", values=(
                t.get("date_time"),
                t.get("type"),
                format_currency(t.get("amount")),
                format_currency(t.get("balance_after"))
            ))


class AccountDetailsView(BaseView):
    """Account Profile Screen with Masked Information."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("👤 ACCOUNT DETAILS")

        self.card = tk.Frame(self, bg=CARD_BG, padx=30, pady=24)
        self.card.pack(pady=30, padx=40, fill="x")

        self.info_labels = {}
        for field in ["Name", "User ID", "Phone", "Account No.", "Balance"]:
            row = tk.Frame(self.card, bg=CARD_BG)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=f"{field}:", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG, width=14, anchor="w").pack(side="left")
            val_lbl = tk.Label(row, text="-", font=("Segoe UI", 11, "bold"), fg=TEXT_WHITE, bg=CARD_BG)
            val_lbl.pack(side="right")
            self.info_labels[field] = val_lbl

        tk.Button(self, text="Back to Dashboard", font=("Segoe UI", 11), bg=CARD_BG, fg=TEXT_WHITE,
                  command=lambda: controller.show_view("DashboardView")).pack(pady=10)

    def on_show(self):
        user = self.controller.current_user
        if user:
            self.info_labels["Name"].config(text=user.get("username", "N/A"))
            self.info_labels["User ID"].config(text=user.get("user_id", "N/A"), fg=ACCENT_BLUE)
            self.info_labels["Phone"].config(text=mask_phone(user.get("phone", "")))
            self.info_labels["Account No."].config(text=mask_account_number(user.get("acc_no", "")), fg="#f59e0b")
            self.info_labels["Balance"].config(text=format_currency(user.get("avl_bal", 0.0)), fg=ACCENT_GREEN)


class ChangePinView(BaseView):
    """PIN Management Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("🔑 CHANGE PIN")

        card = tk.Frame(self, bg=CARD_BG, padx=30, pady=24)
        card.pack(pady=30)

        tk.Label(card, text="Current PIN:", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.old_pin = tk.Entry(card, font=("Segoe UI", 14), show="*", width=18, justify="center")
        self.old_pin.pack(pady=(2, 10))

        tk.Label(card, text="New 4-Digit PIN:", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.new_pin = tk.Entry(card, font=("Segoe UI", 14), show="*", width=18, justify="center")
        self.new_pin.pack(pady=(2, 10))

        tk.Label(card, text="Confirm New PIN:", font=("Segoe UI", 11), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
        self.conf_pin = tk.Entry(card, font=("Segoe UI", 14), show="*", width=18, justify="center")
        self.conf_pin.pack(pady=(2, 16))

        tk.Button(card, text="Update PIN", font=("Segoe UI", 12, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
                  padx=16, pady=8, cursor="hand2", command=self.do_change_pin).pack(fill="x", pady=4)

        tk.Button(card, text="Cancel", font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_MUTED,
                  command=lambda: controller.show_view("DashboardView")).pack(fill="x")

    def do_change_pin(self):
        user = self.controller.current_user
        old = self.old_pin.get().strip()
        new = self.new_pin.get().strip()
        conf = self.conf_pin.get().strip()

        if old != str(user.get("pin")):
            messagebox.showerror("Error", "Current PIN is incorrect.")
            return

        if len(new) != PIN_LENGTH or not new.isdigit():
            messagebox.showerror("Error", f"New PIN must contain exactly {PIN_LENGTH} numeric digits.")
            return

        if new == old:
            messagebox.showerror("Error", "New PIN cannot be identical to the old PIN.")
            return

        if new != conf:
            messagebox.showerror("Error", "Confirmation PIN does not match.")
            return

        user["pin"] = new
        self.controller.storage.save_user(user["user_id"], user)
        messagebox.showinfo("Success", "✔ PIN changed successfully!")
        self.old_pin.delete(0, tk.END)
        self.new_pin.delete(0, tk.END)
        self.conf_pin.delete(0, tk.END)
        self.controller.show_view("DashboardView")


class RegisterView(BaseView):
    """User Onboarding Screen."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.create_header("➕ REGISTER NEW USER")

        card = tk.Frame(self, bg=CARD_BG, padx=30, pady=20)
        card.pack(pady=20)

        self.entries = {}
        fields = [
            ("Full Name", "username", False),
            ("Phone Number", "phone", False),
            ("Account Number", "acc_no", False),
            ("4-Digit PIN", "pin", True),
            ("User ID (e.g. U115)", "user_id", False),
            ("Initial Balance (₹)", "balance", False)
        ]

        for label, key, is_secret in fields:
            tk.Label(card, text=f"{label}:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")
            ent = tk.Entry(card, font=("Segoe UI", 12), show="*" if is_secret else "", width=26)
            ent.pack(pady=(2, 6))
            self.entries[key] = ent

        tk.Button(card, text="Create Account", font=("Segoe UI", 11, "bold"), bg=ACCENT_GREEN, fg=BG_DARK,
                  padx=16, pady=8, cursor="hand2", command=self.do_register).pack(fill="x", pady=(10, 4))

        tk.Button(card, text="Cancel", font=("Segoe UI", 10), bg=CARD_BG, fg=TEXT_MUTED,
                  command=lambda: controller.show_view("LoginView")).pack(fill="x")

    def do_register(self):
        uname = self.entries["username"].get().strip()
        phone = self.entries["phone"].get().strip()
        acc = self.entries["acc_no"].get().strip()
        pin = self.entries["pin"].get().strip()
        uid = self.entries["user_id"].get().strip().upper()
        bal_raw = self.entries["balance"].get().strip()

        if not all([uname, phone, acc, pin, uid, bal_raw]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            bal = float(bal_raw)
            if bal < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Initial balance must be a non-negative number.")
            return

        if len(pin) != PIN_LENGTH or not pin.isdigit():
            messagebox.showerror("Error", f"PIN must contain exactly {PIN_LENGTH} digits.")
            return

        all_users = self.controller.storage.load_data()
        if uid in all_users:
            messagebox.showerror("Error", f"User ID '{uid}' is already taken.")
            return

        if any(u.get("acc_no") == acc for u in all_users.values()):
            messagebox.showerror("Error", "Account number is already registered.")
            return

        new_record = {
            "username": uname,
            "phone": phone,
            "acc_no": acc,
            "pin": pin,
            "user_id": uid,
            "avl_bal": bal,
            "history": {"withdraw_history": [], "deposit_history": []}
        }
        self.controller.storage.save_user(uid, new_record)
        messagebox.showinfo("Success", f"✔ User '{uname}' successfully registered with ID {uid}!")
        self.controller.show_view("LoginView")


def main():
    app = ATMGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
