"""
User management module: authentication, session handling, PIN change,
account details viewing, and new user onboarding.
"""
from config import MAX_LOGIN_ATTEMPTS, PIN_LENGTH
from utils import (
    print_header,
    print_divider,
    print_success,
    print_error,
    print_warning,
    format_currency,
    mask_account_number,
    mask_phone,
    get_masked_pin,
    get_non_empty_string,
    get_safe_float,
    Fore,
    Style
)


def login(storage):
    """
    Authenticates a user with a maximum of 3 attempts.
    Fixes the original KeyError bug by safely checking dictionary keys.
    Returns the authenticated user dict on success, or None on failure/lockout.
    """
    attempts_remaining = MAX_LOGIN_ATTEMPTS
    
    while attempts_remaining > 0:
        print_header("🏧 ATM LOGIN", width=44)
        print(f"Attempts remaining: {attempts_remaining}\n")
        
        user_id = input(f"{Fore.WHITE}User ID : {Style.RESET_ALL}").strip()
        if not user_id:
            print_error("User ID cannot be empty.")
            continue
            
        pin = get_masked_pin(f"{Fore.WHITE}PIN     : {Style.RESET_ALL}")
        
        print("\nChecking credentials...")
        
        # Reload latest data from storage
        all_users = storage.load_data()
        
        # Safe check avoiding KeyError
        if user_id in all_users:
            user_data = all_users[user_id]
            # Ensure PIN is compared as string
            if str(user_data.get("pin")) == pin:
                print()
                print_divider(44)
                print_success("Login Successful!")
                print(f"\nWelcome, {Style.BRIGHT}{user_data.get('username')}{Style.RESET_ALL} 👋")
                print_divider(44)
                return user_data
        
        # If authentication failed
        attempts_remaining -= 1
        print_error("Invalid User ID or PIN.")
        
        if attempts_remaining > 0:
            print_warning(f"You have {attempts_remaining} attempt(s) left before session lockout.\n")
        else:
            print()
            print_divider(44)
            print_error("Maximum 3 login attempts exceeded.")
            print_error("Your ATM session has been locked for security reasons.")
            print_divider(44)
            return None


def show_account_details(user):
    """
    Displays the user's account details with sensitive numbers masked.
    Never exposes the PIN.
    """
    print_header("👤 ACCOUNT DETAILS", width=46)
    print(f"{Fore.WHITE}{'Name':<16}: {Fore.CYAN}{user.get('username', 'N/A')}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'Phone':<16}: {Fore.YELLOW}{mask_phone(user.get('phone', ''))}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'Account No.':<16}: {Fore.YELLOW}{mask_account_number(user.get('acc_no', ''))}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'User ID':<16}: {Fore.CYAN}{user.get('user_id', 'N/A')}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'Balance':<16}: {Fore.GREEN}{format_currency(user.get('avl_bal', 0.0))}{Style.RESET_ALL}")
    print_divider(46)


def change_pin(user, storage):
    """
    Safely changes the user's PIN after verifying current PIN, validating
    4 digits, matching confirmation, and ensuring it differs from the old PIN.
    """
    print_header("🔑 CHANGE PIN", width=46)
    
    # 1. Ask and verify current PIN
    current_pin_input = get_masked_pin("Enter Current PIN : ")
    if current_pin_input != str(user.get("pin")):
        print_error("Current PIN does not match! PIN change canceled.")
        return False
        
    # 2. Ask new PIN
    new_pin = get_masked_pin("Enter New PIN (4 digits): ")
    
    # Validate exactly 4 digits
    if len(new_pin) != PIN_LENGTH or not new_pin.isdigit():
        print_error(f"New PIN must contain exactly {PIN_LENGTH} digits.")
        return False
        
    # Ensure new PIN is different from old PIN
    if new_pin == str(user.get("pin")):
        print_error("New PIN cannot be the same as your old PIN.")
        return False
        
    # 3. Ask confirmation PIN
    confirm_pin = get_masked_pin("Confirm New PIN : ")
    if new_pin != confirm_pin:
        print_error("New PIN and Confirm PIN do not match! PIN change canceled.")
        return False
        
    # 4. Save the new PIN
    user["pin"] = new_pin
    storage.save_user(user["user_id"], user)
    print()
    print_success("PIN changed successfully.")
    print_divider(46)
    return True


def add_new_user(storage):
    """
    Registers a new user into the ATM system with complete validation.
    Fixes the original code's bugs where user_id1 was used as a string literal
    and initial balance was unparsed.
    """
    print_header("👤 REGISTER NEW ATM USER", width=50)
    all_users = storage.load_data()
    
    # User ID validation (must be unique)
    while True:
        user_id = get_non_empty_string("Enter User ID (e.g. A115): ", "User ID").upper()
        if user_id in all_users:
            print_error(f"User ID '{user_id}' already exists. Please choose a different ID.")
            continue
        break
        
    username = get_non_empty_string("Enter Full Name: ", "Username")
    
    # Phone validation
    while True:
        phone = get_non_empty_string("Enter Phone Number: ", "Phone")
        if not phone.isdigit():
            print_error("Phone number must contain only numbers.")
            continue
        break
        
    # Account number validation (must be unique)
    while True:
        acc_no = get_non_empty_string("Enter Account Number: ", "Account Number")
        if not acc_no.isdigit():
            print_error("Account number must contain only numbers.")
            continue
        # Check if already in use
        if any(u.get("acc_no") == acc_no for u in all_users.values()):
            print_error("Account number is already associated with another user.")
            continue
        break
        
    # PIN validation (4 digits)
    while True:
        pin = get_masked_pin("Enter 4-Digit PIN: ")
        if len(pin) != PIN_LENGTH or not pin.isdigit():
            print_error(f"PIN must contain exactly {PIN_LENGTH} numeric digits.")
            continue
        confirm_pin = get_masked_pin("Confirm 4-Digit PIN: ")
        if pin != confirm_pin:
            print_error("PINs do not match. Please try entering PIN again.")
            continue
        break
        
    # Initial balance validation (non-negative)
    init_bal = get_safe_float("Enter Initial Deposit Balance (₹): ", min_val=0.0)
    
    # Create the new user object
    new_user_record = {
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
    
    # Save properly using user_id as dictionary key
    storage.save_user(user_id, new_user_record)
    
    print()
    print_divider(50)
    print_success("New user created successfully!")
    print(f"\nUser ID : {Fore.YELLOW}{user_id}{Style.RESET_ALL}")
    print(f"Name    : {Fore.CYAN}{username}{Style.RESET_ALL}")
    print(f"Balance : {Fore.GREEN}{format_currency(init_bal)}{Style.RESET_ALL}")
    print(f"\nWelcome to ATM Banking System.")
    print_divider(50)
    return new_user_record
