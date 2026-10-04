"""
Configuration file for the ATM Management System.
Contains default seed data, ATM operating rules, and file paths.
"""
import os

# Base directory of the ATM project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data storage paths
DATA_FILE_JSON = os.path.join(BASE_DIR, "users.json")
DB_FILE_SQLITE = os.path.join(BASE_DIR, "atm.db")

# ATM Operating Rules
ATM_NOTE_DENOMINATION = 500       # Only Rs. 500 notes available/accepted
MIN_DEPOSIT_AMOUNT = 3000         # Deposits must be greater than Rs. 3,000
MAX_LOGIN_ATTEMPTS = 3            # Lock session after 3 consecutive failures
PIN_LENGTH = 4                    # PIN must be exactly 4 digits

# Quick withdraw predefined amounts
QUICK_WITHDRAW_OPTIONS = [500, 1000, 2000, 5000, 10000]

# Default Seed Users
DEFAULT_USERS = {
    "A111": {
        "username": "Anjali",
        "phone": "1234",
        "acc_no": "452452",
        "pin": "1414",
        "user_id": "A111",
        "avl_bal": 10000.0,
        "history": {
            "withdraw_history": [],
            "deposit_history": []
        }
    },
    "H112": {
        "username": "Honey",
        "phone": "1244",
        "acc_no": "784152",
        "pin": "2563",
        "user_id": "H112",
        "avl_bal": 20000.0,
        "history": {
            "withdraw_history": [],
            "deposit_history": []
        }
    },
    "H113": {
        "username": "Harsh",
        "phone": "1734",
        "acc_no": "748596",
        "pin": "4785",
        "user_id": "H113",
        "avl_bal": 25000.0,
        "history": {
            "withdraw_history": [],
            "deposit_history": []
        }
    },
    "K114": {
        "username": "Keval",
        "phone": "1234",
        "acc_no": "965263",
        "pin": "0125",
        "user_id": "K114",
        "avl_bal": 80000.0,
        "history": {
            "withdraw_history": [],
            "deposit_history": []
        }
    }
}
