# 🏧 ATM Banking Management System

> A complete, realistic, beginner-friendly Python ATM Banking Management System that simulates common ATM operations such as secure authentication, cash withdrawal, cash deposit, quick withdrawal, balance inquiry, mini statement generation, transaction history, PIN management, and persistent storage across sessions.

---

## 📌 Features

1. **🔐 Secure Login System**:
   - Up to 3 login attempts with automatic security lockout.
   - Hidden PIN entry using Python's `getpass` module (with fallback for automated runners).
   - Safe credential verification without crashing on non-existent accounts.
   - Stores session state so you don't repeatedly enter your User ID.

2. **💰 Cash Withdrawal**:
   - Strict denomination enforcement: ATM only holds ₹500 notes (`amount % 500 == 0`).
   - Insufficient balance validation.
   - Real-time balance updates with a generated transaction receipt.

3. **💵 Cash Deposit**:
   - Minimum deposit threshold (> ₹3,000).
   - Only ₹500 denomination notes accepted.
   - Instant balance credit with a generated deposit receipt.

4. **⚡ Quick Withdraw**:
   - Preset one-touch withdrawal shortcuts: ₹500, ₹1,000, ₹2,000, ₹5,000, ₹10,000.
   - Option for custom amounts or instant cancellation.

5. **💳 Account Balance & Details**:
   - Formatted balance card with Indian Rupee (`₹`) styling.
   - Sensitive information masking (`Account No: ******452452`, `Phone: ****1234`).
   - PIN is never displayed anywhere on screen.

6. **📜 Transaction History & Mini Statement**:
   - Separate withdrawal history and deposit history tables with total sums.
   - Combined **Mini Statement** displaying recent transactions ordered newest first.

7. **🔑 PIN Management**:
   - Verify current PIN.
   - Validates that the new PIN is exactly 4 numeric digits.
   - Prevents re-using the old PIN.
   - Confirms matching entry before persisting.

8. **👤 New User Registration**:
   - Onboard new accounts with unique User ID and unique Account Number validation.
   - Non-negative initial deposit support.

9. **🧹 Clear Transaction History**:
   - Clear withdrawal history, deposit history, or all records with a confirmation prompt.

10. **💾 Dual Storage Persistence**:
    - **JSON Mode (Default)**: Automatically reads and writes to `users.json`.
    - **SQLite Mode**: Full relational database backend (`atm.db`) with `users` and `transactions` tables.

---

## 👥 Sample Login Credentials

| Username | User ID | PIN | Phone | Account No. | Starting Balance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Anjali** | `A111` | `1414` | 1234 | 452452 | ₹10,000 |
| **Honey** | `H112` | `2563` | 1244 | 784152 | ₹20,000 |
| **Harsh** | `H113` | `4785` | 1734 | 748596 | ₹25,000 |
| **Keval** | `K114` | `0125` | 1234 | 965263 | ₹80,000 |

*(Note: Keval's PIN begins with a leading zero `0125`, which is preserved properly as a string).*

---

## 🛠️ Project Structure

```text
e:/atm system/
│
├── main.py              # Application entry point and interactive menu loop
├── atm.py               # Core ATM logic (withdraw, deposit, balance, statements)
├── user.py              # User authentication, change PIN, registration
├── transaction.py       # Transaction models, ID generator, receipts & statements
├── storage.py           # Storage engine abstraction (JSON and SQLite)
├── server.py            # Zero-dependency Web Kiosk REST API server
├── gui.py               # Standalone native desktop GUI application
├── static/              # Web Frontend assets
│   ├── index.html       # Realistic touchscreen ATM Kiosk single-page application
│   ├── css/style.css    # Modern dark-mode ATM kiosk styling & animations
│   └── js/app.js        # Controller, Web Audio synthesizer, and keypad handler
├── utils.py             # Console UI styling, box drawing, currency formatting, masking
├── config.py            # Operating rules, seed users, and file path configurations
├── tests.py             # Comprehensive automated unit test suite
├── users.json           # Default JSON data file (auto-generated)
├── requirements.txt     # Optional dependencies (colorama)
└── README.md            # Documentation and user guides
```

---

## 🚀 How to Run

### Option 1: Modern Web Frontend (Recommended)
Start the built-in web server:
```bash
python server.py
```
Then open your browser to **`http://127.0.0.1:8080`**.
*(Features full ATM touchscreen kiosk, animated card slot, 3D hardware keypad with click sounds, animated cash dispenser with ejecting ₹500 bills, and thermal receipt printer slip).*

---

### Option 2: Native Desktop GUI
Run as a standalone desktop window:
```bash
python gui.py
```
*(Uses Python's standard `tkinter` library — no pip dependencies required).*

---

### Option 3: Terminal Console Mode
Run in your command line:
```bash
# Standard JSON storage
python main.py

# Relational SQLite database storage
python main.py --db
```

---

### Option 4: Run Automated Tests
```bash
python tests.py
```

---

## 🐛 Bugs Fixed from the Original Prototype

| Bug # | Original Code Issue | Solution in Updated System |
| :--- | :--- | :--- |
| **1** | `user_data[id]` caused a fatal `KeyError` on invalid user ID. | Added safe lookup (`id in all_users`) with graceful error handling and retry loop. |
| **2** | `if amount/500:` checked float truthiness rather than divisibility. | Replaced with modulo check `if amount % 500 == 0:`. |
| **3** | Typo `/n` in console message string instead of `\n`. | Replaced with proper escape sequences and multi-line banners. |
| **4** | Unbound identifier `A` at the end of `avilablebalance()` threw `NameError`. | Removed stray identifier and added currency formatting. |
| **5** | `user_data["user_id1"] = new_user` used literal string `"user_id1"`. | Fixed dictionary key assignment using the variable `user_id1`. |
| **6** | `add_user` stored unparsed string balance. | Converted balance into validated float (`min_val=0.0`). |
| **7** | Repeatedly asked for User ID before every operation. | Introduced authenticated session tracking (`current_user`). |
| **8** | Unrecognized menu input fell through to `"......"`. | Replaced with validated input selector (`get_safe_int(min_val=1, max_val=13)`). |
| **9** | Sensitive account numbers and PINs were printed in plaintext. | Implemented masking for phone & account numbers and masked PIN entry. |
| **10** | No data persistence across restarts. | Built dual storage engine (`users.json` and SQLite `atm.db`). |

---

## 🎨 Screenshots / Terminal Preview

```text
╔════════════════════════════════════════════════╗
║        🏧 ATM BANKING MANAGEMENT SYSTEM        ║
╚════════════════════════════════════════════════╝
Storage Engine: JSON File (users.json)

  1. 🔐 User Login
  2. 👤 Register New User
  3. ❌ Exit System

Please select an option (1-3): 1

╔══════════════════════════════════════════╗
║               🏧 ATM LOGIN               ║
╚══════════════════════════════════════════╝
Attempts remaining: 3

User ID : A111
PIN     : ****

Checking credentials...
✔ Login Successful!

╔════════════════════════════════════════════╗
║            🏧 ATM BANKING SYSTEM           ║
╠════════════════════════════════════════════╣
║                                            ║
║  Welcome, Anjali 👋                        ║
║                                            ║
║  1. 💰 Withdraw Money                      ║
║  2. 💵 Deposit Money                       ║
║  3. ⚡ Quick Withdraw                      ║
║  4. 💳 Check Balance                       ║
║  5. 👤 Account Details                     ║
║  6. 📜 Withdraw History                    ║
║  7. 📥 Deposit History                     ║
║  8. 📄 Mini Statement                      ║
║  9. 🔑 Change PIN                          ║
║  10. 🧹 Clear History                      ║
║  11. ➕ Add New User                       ║
║  12. 🚪 Logout                             ║
║  13. ❌ Exit ATM                           ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

## 🖥️ Future Roadmap: Converting to CustomTkinter GUI

The code architecture was designed to allow a seamless conversion into a modern GUI with `CustomTkinter`:

1. **Separation of Concerns**:
   - `atm.py`, `storage.py`, `transaction.py`, and `user.py` contain pure business logic and data persistence without any hardcoded console input coupling.
2. **GUI Views to Implement**:
   - **`App`**: Main window extending `customtkinter.CTk`.
   - **`LoginFrame`**: `CTkEntry` for User ID, `show="*"` for PIN, "Login" and "Register" buttons.
   - **`DashboardFrame`**: Sidebar with navigation buttons (Withdraw, Deposit, Quick Withdraw, Balance, History, Settings, Logout).
   - **`BalanceCard`**: Prominent card widget displaying `format_currency(user['avl_bal'])` and masked account details.
   - **`TransactionTable`**: `CTkScrollableFrame` rendering rows with colored badges (green for deposits, red for withdrawals).
   - **`QuickWithdrawGrid`**: 2x3 button grid for preset amounts (₹500, ₹1000, ₹2000, ₹5000, ₹10000).
3. **Data Binding**:
   - The GUI controllers can directly call `atm.withdraw(current_user, storage)` and update the reactive label widgets upon return.
