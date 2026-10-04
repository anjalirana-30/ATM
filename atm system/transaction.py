"""
Transaction handling, ID generation, timestamp recording, and receipt/statement formatting.
"""
from datetime import datetime
from utils import (
    format_currency,
    print_header,
    print_divider,
    print_success,
    Fore,
    Style
)


def get_current_datetime():
    """Returns current date and time formatted as DD-MM-YYYY HH:MM:SS."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def generate_transaction_id(all_users_data):
    """
    Generates a unique, non-duplicating sequential Transaction ID (e.g. TXN10001, TXN10002).
    Scans existing transactions across all users to guarantee uniqueness.
    """
    highest_num = 10000
    for udata in all_users_data.values():
        history = udata.get("history", {})
        all_txns = history.get("withdraw_history", []) + history.get("deposit_history", [])
        for t in all_txns:
            tid = t.get("txn_id", "")
            if tid.startswith("TXN"):
                try:
                    num = int(tid.replace("TXN", ""))
                    if num > highest_num:
                        highest_num = num
                except ValueError:
                    continue
    return f"TXN{highest_num + 1}"


def create_transaction(txn_id, txn_type, amount, balance_after):
    """Creates a standard transaction record dictionary."""
    return {
        "txn_id": txn_id,
        "type": txn_type,
        "amount": float(amount),
        "date_time": get_current_datetime(),
        "balance_after": float(balance_after)
    }


def print_withdraw_receipt(txn):
    """Displays a formatted receipt after a successful withdrawal."""
    print()
    print_divider(48)
    print_success("Transaction Successful")
    print()
    print(f"{Fore.WHITE}Transaction ID : {Fore.YELLOW}{txn['txn_id']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Amount         : {Fore.GREEN}{format_currency(txn['amount'])}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Remaining      : {Fore.CYAN}{format_currency(txn['balance_after'])}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Date & Time    : {Fore.WHITE}{txn['date_time']}{Style.RESET_ALL}")
    print()
    print(f"{Fore.GREEN}{Style.BRIGHT}Please collect your cash.{Style.RESET_ALL}")
    print_divider(48)


def print_deposit_receipt(txn):
    """Displays a formatted receipt after a successful deposit."""
    print()
    print_divider(48)
    print_success("Deposit Successful")
    print()
    print(f"{Fore.WHITE}Transaction ID : {Fore.YELLOW}{txn['txn_id']}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Deposited      : {Fore.GREEN}{format_currency(txn['amount'])}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}New Balance    : {Fore.CYAN}{format_currency(txn['balance_after'])}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Date & Time    : {Fore.WHITE}{txn['date_time']}{Style.RESET_ALL}")
    print_divider(48)


def display_withdraw_history(withdraw_list):
    """Displays a formatted table of all withdrawals for the logged-in user."""
    print_header("📜 WITHDRAW HISTORY", width=52)
    if not withdraw_list:
        print(f"\n{Fore.YELLOW}No withdrawal transactions found.{Style.RESET_ALL}\n")
        print_divider(52)
        return

    print(f"{'Transaction ID':<16}{'Date & Time':<22}{'Amount':>14}")
    print("─" * 52)
    total_withdrawn = 0.0
    for t in withdraw_list:
        amt = float(t.get("amount", 0))
        total_withdrawn += amt
        tid = t.get("txn_id", "N/A")
        dt = t.get("date_time", "N/A")
        print(f"{tid:<16}{dt:<22}{format_currency(amt):>14}")

    print("─" * 52)
    print(f"{Style.BRIGHT}Total Withdrawn: {Fore.GREEN}{format_currency(total_withdrawn)}{Style.RESET_ALL}")
    print_divider(52)


def display_deposit_history(deposit_list):
    """Displays a formatted table of all deposits for the logged-in user."""
    print_header("📥 DEPOSIT HISTORY", width=52)
    if not deposit_list:
        print(f"\n{Fore.YELLOW}No deposit transactions found.{Style.RESET_ALL}\n")
        print_divider(52)
        return

    print(f"{'Transaction ID':<16}{'Date & Time':<22}{'Amount':>14}")
    print("─" * 52)
    total_deposited = 0.0
    for t in deposit_list:
        amt = float(t.get("amount", 0))
        total_deposited += amt
        tid = t.get("txn_id", "N/A")
        dt = t.get("date_time", "N/A")
        print(f"{tid:<16}{dt:<22}{format_currency(amt):>14}")

    print("─" * 52)
    print(f"{Style.BRIGHT}Total Deposited: {Fore.GREEN}{format_currency(total_deposited)}{Style.RESET_ALL}")
    print_divider(52)


def display_mini_statement(withdraw_list, deposit_list, current_balance, max_entries=10):
    """
    Displays a combined transaction statement showing latest transactions first.
    """
    print_header("📄 MINI STATEMENT", width=52)

    # Combine both lists and ensure all records have a timestamp for sorting
    combined = []
    for item in withdraw_list:
        item_copy = dict(item)
        item_copy["display_type"] = "Withdraw"
        combined.append(item_copy)

    for item in deposit_list:
        item_copy = dict(item)
        item_copy["display_type"] = "Deposit"
        combined.append(item_copy)

    if not combined:
        print(f"\n{Fore.YELLOW}No transaction history available.{Style.RESET_ALL}\n")
        print("─" * 52)
        print(f"{Style.BRIGHT}Current Balance: {Fore.CYAN}{format_currency(current_balance)}{Style.RESET_ALL}")
        print_divider(52)
        return

    # Sort latest first (reverse chronological order)
    def parse_date(x):
        try:
            return datetime.strptime(x.get("date_time", ""), "%d-%m-%Y %H:%M:%S")
        except Exception:
            return datetime.min

    combined.sort(key=parse_date, reverse=True)
    latest_txns = combined[:max_entries]

    print(f"{'Date & Time':<22}{'Type':<14}{'Amount':>16}")
    print("─" * 52)

    for t in latest_txns:
        dt = t.get("date_time", "N/A")
        ttype = t.get("display_type", t.get("type", "N/A"))
        amt = float(t.get("amount", 0))
        color = Fore.RED if ttype.lower() == "withdraw" else Fore.GREEN
        print(f"{dt:<22}{ttype:<14}{color}{format_currency(amt):>16}{Style.RESET_ALL}")

    print("─" * 52)
    print(f"{Style.BRIGHT}Current Balance: {Fore.CYAN}{format_currency(current_balance)}{Style.RESET_ALL}")
    print_divider(52)
