"""
Main Entry Point for the ATM Management System.
Connects the user authentication, ATM operations, persistence layer,
and interactive console menus.
"""
import sys
import argparse
from config import DATA_FILE_JSON, DB_FILE_SQLITE
from storage import JSONStorage, SQLiteStorage
from utils import (
    print_header,
    print_divider,
    print_success,
    print_warning,
    print_info,
    print_error,
    pause,
    get_safe_int,
    Fore,
    Style
)
from user import login, show_account_details, change_pin, add_new_user
from atm import (
    show_balance,
    withdraw,
    deposit,
    quick_withdraw,
    show_withdraw_history,
    show_deposit_history,
    show_mini_statement,
    clear_history
)


def display_main_menu(username):
    """Renders the styled ATM dashboard menu."""
    width = 46
    print()
    print(f"{Fore.CYAN}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{Style.BRIGHT}{Fore.WHITE}{'🏧 ATM BANKING SYSTEM'.center(width - 2)}{Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╠{'═' * (width - 2)}╣{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
    welcome_text = f"  Welcome, {username} 👋"
    print(f"{Fore.CYAN}║{Style.BRIGHT}{Fore.YELLOW}{welcome_text.ljust(width - 2)}{Style.RESET_ALL}{Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
    
    menu_items = [
        "1. 💰 Withdraw Money",
        "2. 💵 Deposit Money",
        "3. ⚡ Quick Withdraw",
        "4. 💳 Check Balance",
        "5. 👤 Account Details",
        "6. 📜 Withdraw History",
        "7. 📥 Deposit History",
        "8. 📄 Mini Statement",
        "9. 🔑 Change PIN",
        "10. 🧹 Clear History",
        "11. ➕ Add New User",
        "12. 🚪 Logout",
        "13. ❌ Exit ATM"
    ]
    
    for item in menu_items:
        print(f"{Fore.CYAN}║  {Fore.WHITE}{item.ljust(width - 5)}{Fore.CYAN}║{Style.RESET_ALL}")
        
    print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")


def session_loop(current_user, storage):
    """
    Main interactive loop for the authenticated user session.
    Transactions automatically belong to current_user without re-prompting for user ID.
    """
    while True:
        display_main_menu(current_user.get("username", "Customer"))
        choice = get_safe_int("Select an option (1-13): ", min_val=1, max_val=13)
        
        if choice == 1:
            withdraw(current_user, storage)
            pause()
        elif choice == 2:
            deposit(current_user, storage)
            pause()
        elif choice == 3:
            quick_withdraw(current_user, storage)
            pause()
        elif choice == 4:
            show_balance(current_user)
            pause()
        elif choice == 5:
            show_account_details(current_user)
            pause()
        elif choice == 6:
            show_withdraw_history(current_user)
            pause()
        elif choice == 7:
            show_deposit_history(current_user)
            pause()
        elif choice == 8:
            show_mini_statement(current_user)
            pause()
        elif choice == 9:
            change_pin(current_user, storage)
            pause()
        elif choice == 10:
            clear_history(current_user, storage)
            pause()
        elif choice == 11:
            add_new_user(storage)
            pause()
        elif choice == 12:
            # Logout
            print()
            print_divider(44)
            print_info("Logging out...")
            print(f"Thank you, {Fore.CYAN}{current_user.get('username')}{Style.RESET_ALL}! 👋")
            print("Returning to login screen...")
            print_divider(44)
            pause()
            break
        elif choice == 13:
            # Exit ATM
            print_exit_message()
            sys.exit(0)


def print_exit_message():
    """Prints a friendly exit banner."""
    print()
    print_header("Thank you for using our ATM!", width=48)
    print(f"{Fore.YELLOW}{Style.BRIGHT}{'Have a nice day! 👋'.center(48)}{Style.RESET_ALL}")
    print_divider(48)
    print()


def main():
    """Application startup orchestrator."""
    parser = argparse.ArgumentParser(description="ATM Management System")
    parser.add_argument("--db", action="store_true", help="Use SQLite database storage instead of JSON")
    args = parser.parse_args()

    # Initialize storage engine
    if args.db:
        storage = SQLiteStorage()
        storage_type = "SQLite Database (atm.db)"
    else:
        storage = JSONStorage()
        storage_type = "JSON File (users.json)"

    while True:
        print_header("🏧 ATM BANKING MANAGEMENT SYSTEM", width=50)
        print(f"{Fore.CYAN}Storage Engine: {Fore.YELLOW}{storage_type}{Style.RESET_ALL}\n")
        print("  1. 🔐 User Login")
        print("  2. 👤 Register New User")
        print("  3. ❌ Exit System")
        print()

        choice = get_safe_int("Please select an option (1-3): ", min_val=1, max_val=3)

        if choice == 1:
            user = login(storage)
            if user:
                session_loop(user, storage)
            else:
                # 3 failed attempts or lockout
                print_warning("Returning to welcome screen...")
                pause()
        elif choice == 2:
            add_new_user(storage)
            pause()
        elif choice == 3:
            print_exit_message()
            break


if __name__ == "__main__":
    main()
