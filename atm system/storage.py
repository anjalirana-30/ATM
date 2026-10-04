"""
Storage layer for the ATM Management System.
Supports both JSON file persistence and SQLite database persistence.
"""
import os
import json
import sqlite3
import copy
from config import DATA_FILE_JSON, DB_FILE_SQLITE, DEFAULT_USERS


class JSONStorage:
    """Handles loading and saving ATM user and transaction data to a JSON file."""

    def __init__(self, filepath=DATA_FILE_JSON):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Creates the JSON storage file with default seed users if not already present."""
        if not os.path.exists(self.filepath):
            self.save_data(copy.deepcopy(DEFAULT_USERS))

    def load_data(self):
        """Loads and returns all user data from the JSON file."""
        try:
            if not os.path.exists(self.filepath):
                self._ensure_file_exists()
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, OSError) as e:
            # Fallback to seed data in case of file corruption
            print(f"[Warning] Error loading {self.filepath}: {e}. Initializing default data.")
            fallback = copy.deepcopy(DEFAULT_USERS)
            self.save_data(fallback)
            return fallback

    def save_data(self, data):
        """Persists all user data to the JSON file with atomic write safety."""
        temp_file = f"{self.filepath}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            # Atomic replace
            os.replace(temp_file, self.filepath)
        except OSError:
            # Direct write fallback for Windows locks
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def get_user(self, user_id):
        """Retrieves a single user's record by User ID."""
        data = self.load_data()
        return data.get(user_id)

    def save_user(self, user_id, user_dict):
        """Updates or creates a user's record."""
        data = self.load_data()
        data[user_id] = user_dict
        self.save_data(data)

    def record_transaction(self, user_id, txn_dict):
        """
        Appends a transaction record into the user's history and updates JSON storage.
        txn_dict has keys: txn_id, type ('Withdraw'|'Deposit'), amount, date_time, balance_after
        """
        data = self.load_data()
        if user_id in data:
            user = data[user_id]
            history = user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
            if txn_dict["type"].lower() == "withdraw":
                history.setdefault("withdraw_history", []).append(txn_dict)
            else:
                history.setdefault("deposit_history", []).append(txn_dict)
            self.save_data(data)


class SQLiteStorage:
    """
    Handles persisting ATM users and transactions to an SQLite relational database.
    Satisfies Requirement 22.
    """

    def __init__(self, db_path=DB_FILE_SQLITE):
        self.db_path = db_path
        self._init_db()

    from contextlib import contextmanager

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables and seeds default users if database is newly created."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    phone TEXT,
                    account_number TEXT UNIQUE,
                    pin TEXT NOT NULL,
                    balance REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date_time TEXT NOT NULL,
                    balance_after_transaction REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()

            # Seed users if users table is empty
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                for uid, udata in DEFAULT_USERS.items():
                    cursor.execute("""
                        INSERT INTO users (id, username, phone, account_number, pin, balance)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        uid,
                        udata["username"],
                        udata["phone"],
                        udata["acc_no"],
                        udata["pin"],
                        float(udata["avl_bal"])
                    ))
                conn.commit()

    def load_data(self):
        """Converts SQLite tables into the standard dictionary format used by the ATM."""
        data = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

            for u in users:
                uid = u["id"]
                data[uid] = {
                    "user_id": uid,
                    "username": u["username"],
                    "phone": u["phone"],
                    "acc_no": u["account_number"],
                    "pin": u["pin"],
                    "avl_bal": float(u["balance"]),
                    "history": {
                        "withdraw_history": [],
                        "deposit_history": []
                    }
                }

                # Load transactions for this user
                cursor.execute("""
                    SELECT * FROM transactions WHERE user_id = ? ORDER BY date_time ASC
                """, (uid,))
                txns = cursor.fetchall()
                for t in txns:
                    txn_dict = {
                        "txn_id": t["transaction_id"],
                        "type": t["transaction_type"],
                        "amount": float(t["amount"]),
                        "date_time": t["date_time"],
                        "balance_after": float(t["balance_after_transaction"])
                    }
                    if t["transaction_type"].lower() == "withdraw":
                        data[uid]["history"]["withdraw_history"].append(txn_dict)
                    else:
                        data[uid]["history"]["deposit_history"].append(txn_dict)

        return data

    def save_data(self, data):
        """Syncs in-memory dictionary data back to the SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for uid, udata in data.items():
                cursor.execute("""
                    INSERT INTO users (id, username, phone, account_number, pin, balance)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        username = excluded.username,
                        phone = excluded.phone,
                        account_number = excluded.account_number,
                        pin = excluded.pin,
                        balance = excluded.balance
                """, (
                    uid,
                    udata["username"],
                    udata["phone"],
                    udata["acc_no"],
                    udata["pin"],
                    float(udata["avl_bal"])
                ))
            conn.commit()

    def save_user(self, user_id, user_dict):
        """Saves a single user record to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, phone, account_number, pin, balance)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    phone = excluded.phone,
                    account_number = excluded.account_number,
                    pin = excluded.pin,
                    balance = excluded.balance
            """, (
                user_id,
                user_dict["username"],
                user_dict["phone"],
                user_dict["acc_no"],
                user_dict["pin"],
                float(user_dict["avl_bal"])
            ))
            conn.commit()

    def record_transaction(self, user_id, txn_dict):
        """Records a transaction in SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO transactions 
                (transaction_id, user_id, transaction_type, amount, date_time, balance_after_transaction)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                txn_dict["txn_id"],
                user_id,
                txn_dict["type"],
                float(txn_dict["amount"]),
                txn_dict["date_time"],
                float(txn_dict["balance_after"])
            ))
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (float(txn_dict["balance_after"]), user_id))
            conn.commit()

    def clear_user_history(self, user_id, txn_type=None):
        """Clears transactions from SQLite for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if txn_type:
                cursor.execute("DELETE FROM transactions WHERE user_id = ? AND LOWER(transaction_type) = LOWER(?)", (user_id, txn_type))
            else:
                cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            conn.commit()
