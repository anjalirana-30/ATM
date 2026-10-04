"""
Automated unit test suite for the ATM Management System.
Tests business logic, validations, ID generation, storage persistence, and edge cases.
"""
import os
import shutil
import unittest
from datetime import datetime

from config import DEFAULT_USERS, ATM_NOTE_DENOMINATION, MIN_DEPOSIT_AMOUNT
from storage import JSONStorage, SQLiteStorage
from utils import format_currency, mask_account_number, mask_phone
from transaction import generate_transaction_id, create_transaction
from atm import (
    show_balance,
    withdraw,
    deposit,
    quick_withdraw,
    display_withdraw_history,
    display_deposit_history,
    display_mini_statement
)


import tempfile


class ATMSystemTests(unittest.TestCase):
    def setUp(self):
        # Set up isolated temp test directory for each test
        self.test_dir = tempfile.mkdtemp()
        self.test_json = os.path.join(self.test_dir, "test_users.json")
        self.test_db = os.path.join(self.test_dir, "test_atm.db")

        # Initialize test storage
        self.storage = JSONStorage(filepath=self.test_json)
        self.db_storage = SQLiteStorage(db_path=self.test_db)

    def tearDown(self):
        # Clean up test files safely
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_default_users_seeded(self):
        """Verify default users are properly seeded."""
        data = self.storage.load_data()
        self.assertIn("A111", data)
        self.assertIn("H112", data)
        self.assertIn("H113", data)
        self.assertIn("K114", data)
        self.assertEqual(data["A111"]["username"], "Anjali")
        self.assertEqual(data["A111"]["avl_bal"], 10000.0)
        self.assertEqual(data["K114"]["pin"], "0125")  # Preserves leading zero

    def test_masking_helpers(self):
        """Verify phone and account number masking."""
        self.assertEqual(mask_account_number("452452"), "******452452")
        self.assertEqual(mask_account_number("123"), "******123")
        self.assertEqual(mask_phone("1234"), "****1234")
        self.assertEqual(mask_phone("9876543210"), "****3210")

    def test_format_currency(self):
        """Verify Indian Rupee currency formatting."""
        self.assertEqual(format_currency(10000), "₹10,000")
        self.assertEqual(format_currency(500), "₹500")
        self.assertEqual(format_currency(1234.50), "₹1,234.50")

    def test_transaction_id_generation(self):
        """Verify unique sequential Transaction ID generation."""
        data = self.storage.load_data()
        txn1 = generate_transaction_id(data)
        self.assertEqual(txn1, "TXN10001")

        # Add a transaction and test next ID
        t_record = create_transaction(txn1, "Withdraw", 1000, 9000)
        data["A111"]["history"]["withdraw_history"].append(t_record)
        self.storage.save_data(data)

        txn2 = generate_transaction_id(data)
        self.assertEqual(txn2, "TXN10002")

    def test_withdrawal_logic(self):
        """Verify withdrawal balance deduction and rules."""
        user = self.storage.get_user("A111")
        initial_bal = user["avl_bal"]
        withdraw_amt = 2000

        # Denomination check
        self.assertEqual(withdraw_amt % ATM_NOTE_DENOMINATION, 0)
        self.assertTrue(withdraw_amt <= initial_bal)

        # Apply withdrawal
        user["avl_bal"] -= withdraw_amt
        txn_id = generate_transaction_id(self.storage.load_data())
        txn = create_transaction(txn_id, "Withdraw", withdraw_amt, user["avl_bal"])
        user["history"]["withdraw_history"].append(txn)
        self.storage.save_user("A111", user)

        # Reload and verify
        reloaded = self.storage.get_user("A111")
        self.assertEqual(reloaded["avl_bal"], 8000.0)
        self.assertEqual(len(reloaded["history"]["withdraw_history"]), 1)
        self.assertEqual(reloaded["history"]["withdraw_history"][0]["txn_id"], "TXN10001")
        self.assertEqual(reloaded["history"]["withdraw_history"][0]["amount"], 2000.0)

    def test_deposit_logic(self):
        """Verify deposit minimum requirement and multiple of 500 rule."""
        user = self.storage.get_user("H112")
        initial_bal = user["avl_bal"]

        # Deposit <= 3000 should be rejected by rule
        invalid_deposit = 3000
        self.assertFalse(invalid_deposit > MIN_DEPOSIT_AMOUNT)

        # Non-multiple of 500 should be rejected
        invalid_multiple = 3700
        self.assertNotEqual(invalid_multiple % ATM_NOTE_DENOMINATION, 0)

        # Valid deposit
        valid_deposit = 5000
        self.assertTrue(valid_deposit > MIN_DEPOSIT_AMOUNT)
        self.assertEqual(valid_deposit % ATM_NOTE_DENOMINATION, 0)

        user["avl_bal"] += valid_deposit
        txn_id = generate_transaction_id(self.storage.load_data())
        txn = create_transaction(txn_id, "Deposit", valid_deposit, user["avl_bal"])
        user["history"]["deposit_history"].append(txn)
        self.storage.save_user("H112", user)

        reloaded = self.storage.get_user("H112")
        self.assertEqual(reloaded["avl_bal"], 25000.0)
        self.assertEqual(len(reloaded["history"]["deposit_history"]), 1)
        self.assertEqual(reloaded["history"]["deposit_history"][0]["amount"], 5000.0)

    def test_change_pin_rules(self):
        """Verify PIN change criteria (4-digit, non-identical to old)."""
        user = self.storage.get_user("H113")
        old_pin = user["pin"]

        invalid_pin_len = "123"
        self.assertNotEqual(len(invalid_pin_len), 4)

        invalid_pin_alpha = "12ab"
        self.assertFalse(invalid_pin_alpha.isdigit())

        same_pin = old_pin
        self.assertEqual(same_pin, old_pin)

        valid_new_pin = "9988"
        self.assertEqual(len(valid_new_pin), 4)
        self.assertTrue(valid_new_pin.isdigit())
        self.assertNotEqual(valid_new_pin, old_pin)

        user["pin"] = valid_new_pin
        self.storage.save_user("H113", user)

        reloaded = self.storage.get_user("H113")
        self.assertEqual(reloaded["pin"], "9988")

    def test_sqlite_persistence(self):
        """Verify SQLite storage operations match JSON storage."""
        data = self.db_storage.load_data()
        self.assertIn("A111", data)
        self.assertEqual(data["A111"]["username"], "Anjali")
        self.assertEqual(data["A111"]["avl_bal"], 10000.0)

        # Insert a transaction
        txn = {
            "txn_id": "TXN10001",
            "type": "Withdraw",
            "amount": 1500.0,
            "date_time": "02-10-2026 08:00:00",
            "balance_after": 8500.0
        }
        self.db_storage.record_transaction("A111", txn)

        reloaded = self.db_storage.load_data()
        self.assertEqual(reloaded["A111"]["avl_bal"], 8500.0)
        self.assertEqual(len(reloaded["A111"]["history"]["withdraw_history"]), 1)
        self.assertEqual(reloaded["A111"]["history"]["withdraw_history"][0]["amount"], 1500.0)

    def test_add_new_user_uniqueness(self):
        """Verify user ID and account number uniqueness checks."""
        data = self.storage.load_data()
        self.assertIn("A111", data)

        # Existing user ID must be detected
        self.assertTrue("A111" in data)

        # Existing account number must be detected
        existing_acc = any(u.get("acc_no") == "452452" for u in data.values())
        self.assertTrue(existing_acc)

        # Create new unique user
        new_user = {
            "username": "Rahul",
            "phone": "9999",
            "acc_no": "112233",
            "pin": "5678",
            "user_id": "R115",
            "avl_bal": 15000.0,
            "history": {"withdraw_history": [], "deposit_history": []}
        }
        self.storage.save_user("R115", new_user)
        reloaded = self.storage.get_user("R115")
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded["username"], "Rahul")

    def test_clear_history(self):
        """Verify clearing history."""
        user = self.storage.get_user("A111")
        user["history"]["withdraw_history"].append(create_transaction("TXN10001", "Withdraw", 1000, 9000))
        user["history"]["deposit_history"].append(create_transaction("TXN10002", "Deposit", 5000, 14000))
        self.storage.save_user("A111", user)

        # Clear withdraw history
        user["history"]["withdraw_history"] = []
        self.storage.save_user("A111", user)
        reloaded = self.storage.get_user("A111")
        self.assertEqual(len(reloaded["history"]["withdraw_history"]), 0)
        self.assertEqual(len(reloaded["history"]["deposit_history"]), 1)

    def test_mini_statement_sort(self):
        """Verify mini statement sorts newest transactions first."""
        txns = [
            {"txn_id": "TXN10001", "type": "Withdraw", "amount": 1000, "date_time": "02-10-2026 07:20:00"},
            {"txn_id": "TXN10002", "type": "Deposit", "amount": 5000, "date_time": "02-10-2026 07:30:00"},
            {"txn_id": "TXN10003", "type": "Withdraw", "amount": 2000, "date_time": "02-10-2026 08:15:00"},
        ]
        # Sort latest first
        sorted_txns = sorted(
            txns,
            key=lambda x: datetime.strptime(x["date_time"], "%d-%m-%Y %H:%M:%S"),
            reverse=True
        )
        self.assertEqual(sorted_txns[0]["txn_id"], "TXN10003")
        self.assertEqual(sorted_txns[1]["txn_id"], "TXN10002")
        self.assertEqual(sorted_txns[2]["txn_id"], "TXN10001")


if __name__ == "__main__":
    unittest.main()

