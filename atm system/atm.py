"""
Core ATM business operations: Withdraw, Deposit, Quick Withdraw, Balance Inquiry,
Transaction History, Mini Statement, and Clearing History.
"""
from config import (
    ATM_NOTE_DENOMINATION,
    MIN_DEPOSIT_AMOUNT,
    QUICK_WITHDRAW_OPTIONS
)
from utils import (
    print_header,
    print_divider,
    print_success,
    print_error,
    print_warning,
    format_currency,
    mask_account_number,
    get_safe_int,
    get_safe_float,
    Fore,
    Style
)
from transaction import (
    generate_transaction_id,
    create_transaction,
    print_withdraw_receipt,
    print_deposit_receipt,
    display_withdraw_history,
    display_deposit_history,
    display_mini_statement
)


def show_balance(user):
    """
    Displays the user's available balance in a clean card layout with masked account number.
    Satisfies Requirement 10.
    """
    print_header("💳 ACCOUNT BALANCE", width=46)
    print(f"{Fore.WHITE}Account Holder : {Fore.CYAN}{user.get('username')}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Account Number : {Fore.YELLOW}{mask_account_number(user.get('acc_no'))}{Style.RESET_ALL}")
    print()
    print(f"{Fore.WHITE}Available Balance:{Style.RESET_ALL}")
    print()
    print(f"       {Style.BRIGHT}{Fore.GREEN}{format_currency(user.get('avl_bal', 0.0))}{Style.RESET_ALL}")
    print()
    print_divider(46)


def withdraw(user, storage):
    """
    Handles cash withdrawal with proper validation:
    - Amount > 0
    - Multiple of Rs. 500
    - Amount <= Available Balance
    - Updates persistent storage and records transaction
    Fixes original 'if amount/500' logic error.
    """
    print_header("💰 WITHDRAW MONEY", width=48)
    current_bal = float(user.get("avl_bal", 0.0))
    print(f"Available Balance: {Fore.GREEN}{format_currency(current_bal)}{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}Note: ATM dispenses {format_currency(ATM_NOTE_DENOMINATION)} notes only.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}(Enter 0 to cancel withdrawal){Style.RESET_ALL}\n")

    amount = get_safe_int(
        f"Enter amount to withdraw ({format_currency(ATM_NOTE_DENOMINATION)}s): ₹",
        min_val=0,
        allow_cancel=True,
        cancel_value=0
    )

    if amount == 0:
        print_warning("Withdrawal canceled.")
        return False

    # Check sufficient balance
    if amount > current_bal:
        print_error("Insufficient balance in your account.")
        print(f"Your available balance is only {format_currency(current_bal)}.")
        return False

    # Check denomination rule (multiple of 500)
    if amount % ATM_NOTE_DENOMINATION != 0:
        print_error(f"ATM has only {format_currency(ATM_NOTE_DENOMINATION)} notes.")
        print_warning(f"Please enter an amount that is a multiple of {format_currency(ATM_NOTE_DENOMINATION)}.")
        return False

    print("\nProcessing cash withdrawal...")

    # Deduct balance
    user["avl_bal"] = current_bal - amount

    # Generate sequential unique Transaction ID
    all_data = storage.load_data()
    txn_id = generate_transaction_id(all_data)

    # Create transaction object
    txn = create_transaction(txn_id, "Withdraw", amount, user["avl_bal"])

    # Update history in user object
    user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
    user["history"].setdefault("withdraw_history", []).append(txn)

    # Persist updated user state
    storage.save_user(user["user_id"], user)

    # Print transaction receipt
    print_withdraw_receipt(txn)
    return True


def deposit(user, storage):
    """
    Handles cash deposit with proper validation:
    - Amount must be greater than Rs. 3,000
    - Amount must be a multiple of Rs. 500
    - Only Rs. 500 notes accepted
    - Updates persistent storage and records transaction
    """
    print_header("💵 DEPOSIT MONEY", width=48)
    print(f"Current Balance: {Fore.GREEN}{format_currency(user.get('avl_bal', 0.0))}{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}Rules:{Style.RESET_ALL}")
    print(f" • Deposit amount must be greater than {format_currency(MIN_DEPOSIT_AMOUNT)}")
    print(f" • Amount must be in multiples of {format_currency(ATM_NOTE_DENOMINATION)} notes only")
    print(f"{Fore.YELLOW}(Enter 0 to cancel deposit){Style.RESET_ALL}\n")

    amount = get_safe_int(
        f"Enter amount to deposit: ₹",
        min_val=0,
        allow_cancel=True,
        cancel_value=0
    )

    if amount == 0:
        print_warning("Deposit canceled.")
        return False

    # Check minimum deposit requirement (> 3000)
    if amount <= MIN_DEPOSIT_AMOUNT:
        print_error(f"Deposit amount must be strictly greater than {format_currency(MIN_DEPOSIT_AMOUNT)}.")
        return False

    # Check denomination rule (multiple of 500)
    if amount % ATM_NOTE_DENOMINATION != 0:
        print_error(f"Only {format_currency(ATM_NOTE_DENOMINATION)} notes are accepted.")
        print_warning(f"Please deposit an amount in multiples of {format_currency(ATM_NOTE_DENOMINATION)}.")
        return False

    print("\nProcessing cash deposit...")

    # Credit balance
    current_bal = float(user.get("avl_bal", 0.0))
    user["avl_bal"] = current_bal + amount

    # Generate sequential unique Transaction ID
    all_data = storage.load_data()
    txn_id = generate_transaction_id(all_data)

    # Create transaction object
    txn = create_transaction(txn_id, "Deposit", amount, user["avl_bal"])

    # Update history in user object
    user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
    user["history"].setdefault("deposit_history", []).append(txn)

    # Persist updated user state
    storage.save_user(user["user_id"], user)

    # Print transaction receipt
    print_deposit_receipt(txn)
    return True


def quick_withdraw(user, storage):
    """
    Provides fast withdrawal shortcuts for standard denominations.
    Satisfies Requirement 6.
    """
    print_header("⚡ QUICK WITHDRAW", width=46)
    current_bal = float(user.get("avl_bal", 0.0))
    print(f"Available Balance: {Fore.GREEN}{format_currency(current_bal)}{Style.RESET_ALL}\n")

    for i, amt in enumerate(QUICK_WITHDRAW_OPTIONS, 1):
        print(f"  {Fore.YELLOW}{i}.{Style.RESET_ALL} {format_currency(amt)}")

    print(f"  {Fore.YELLOW}6.{Style.RESET_ALL} Other Amount")
    print(f"  {Fore.YELLOW}7.{Style.RESET_ALL} Cancel")
    print()

    choice = get_safe_int("Select Quick Withdraw option (1-7): ", min_val=1, max_val=7)

    if choice == 7:
        print_warning("Quick withdraw canceled.")
        return False

    if choice == 6:
        return withdraw(user, storage)

    selected_amount = QUICK_WITHDRAW_OPTIONS[choice - 1]

    if selected_amount > current_bal:
        print_error("Insufficient balance for this selection.")
        print(f"Selected: {format_currency(selected_amount)} | Available: {format_currency(current_bal)}")
        return False

    print(f"\nDispensing {format_currency(selected_amount)}...")

    # Deduct balance
    user["avl_bal"] = current_bal - selected_amount

    # Generate sequential unique Transaction ID
    all_data = storage.load_data()
    txn_id = generate_transaction_id(all_data)

    # Create transaction object
    txn = create_transaction(txn_id, "Withdraw", selected_amount, user["avl_bal"])

    # Update history
    user.setdefault("history", {"withdraw_history": [], "deposit_history": []})
    user["history"].setdefault("withdraw_history", []).append(txn)

    # Persist updated user state
    storage.save_user(user["user_id"], user)

    # Print transaction receipt
    print_withdraw_receipt(txn)
    return True


def show_withdraw_history(user):
    """Displays withdrawal history for the currently logged-in user."""
    history = user.get("history", {})
    withdraw_list = history.get("withdraw_history", [])
    display_withdraw_history(withdraw_list)


def show_deposit_history(user):
    """Displays deposit history for the currently logged-in user."""
    history = user.get("history", {})
    deposit_list = history.get("deposit_history", [])
    display_deposit_history(deposit_list)


def show_mini_statement(user):
    """Displays combined mini statement sorted newest first."""
    history = user.get("history", {})
    withdraw_list = history.get("withdraw_history", [])
    deposit_list = history.get("deposit_history", [])
    display_mini_statement(withdraw_list, deposit_list, user.get("avl_bal", 0.0))


def clear_history(user, storage):
    """
    Allows user to clear withdrawal history, deposit history, or all history with confirmation.
    Satisfies Requirement 15.
    """
    print_header("🧹 CLEAR TRANSACTION HISTORY", width=48)
    print("1. Clear Withdrawal History")
    print("2. Clear Deposit History")
    print("3. Clear All History")
    print("4. Cancel")
    print()

    choice = get_safe_int("Enter option (1-4): ", min_val=1, max_val=4)

    if choice == 4:
        print_warning("Clear history canceled.")
        return

    # Prompt confirmation
    print("\nAre you sure you want to clear your history?")
    print("1. Yes, Delete")
    print("2. No, Cancel")
    confirm = get_safe_int("Confirm selection (1-2): ", min_val=1, max_val=2)

    if confirm != 1:
        print_warning("Operation canceled. No records were deleted.")
        return

    history = user.setdefault("history", {"withdraw_history": [], "deposit_history": []})

    if choice == 1:
        history["withdraw_history"] = []
        print_success("Withdrawal history has been cleared.")
    elif choice == 2:
        history["deposit_history"] = []
        print_success("Deposit history has been cleared.")
    elif choice == 3:
        history["withdraw_history"] = []
        history["deposit_history"] = []
        print_success("All transaction history has been cleared.")

    storage.save_user(user["user_id"], user)
    print_divider(48)
