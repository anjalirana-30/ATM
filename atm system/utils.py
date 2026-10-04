"""
Utility functions for console styling, currency formatting, masking, and safe input handling.
"""
import os
import sys
import getpass

# Configure stdout and stderr to UTF-8 on Windows to safely print emojis and box-drawing characters
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Safe import for colorama; fall back gracefully if not installed
try:
    import colorama
    from colorama import Fore, Style, Back
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()
    Back = DummyColor()


def clear_screen():
    """Clear terminal screen if supported, otherwise print newlines."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title, width=48):
    """Prints a styled decorative header banner."""
    border_top    = f"{Fore.CYAN}╔{'═' * (width - 2)}╗{Style.RESET_ALL}"
    border_bottom = f"{Fore.CYAN}╚{'═' * (width - 2)}╝{Style.RESET_ALL}"
    
    # Calculate padding for centered text
    inner_width = width - 4
    centered_title = title.center(inner_width)
    content_line = f"{Fore.CYAN}║ {Style.BRIGHT}{Fore.WHITE}{centered_title}{Style.RESET_ALL}{Fore.CYAN} ║{Style.RESET_ALL}"
    
    print()
    print(border_top)
    print(content_line)
    print(border_bottom)


def print_section(title, width=48):
    """Prints a section separator with title."""
    inner = f" {title} "
    total_dashes = max(0, width - len(inner))
    left = total_dashes // 2
    right = total_dashes - left
    print(f"\n{Fore.CYAN}{'═' * left}{Style.BRIGHT}{Fore.YELLOW}{inner}{Style.RESET_ALL}{Fore.CYAN}{'═' * right}{Style.RESET_ALL}")


def print_divider(width=48):
    """Prints a clean divider line."""
    print(f"{Fore.CYAN}{'─' * width}{Style.RESET_ALL}")


def print_success(message):
    """Prints a green success message."""
    print(f"{Fore.GREEN}{Style.BRIGHT}✔ {message}{Style.RESET_ALL}")


def print_error(message):
    """Prints a red error message."""
    print(f"{Fore.RED}{Style.BRIGHT}✘ Error: {message}{Style.RESET_ALL}")


def print_warning(message):
    """Prints a yellow warning message."""
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚠ {message}{Style.RESET_ALL}")


def print_info(message):
    """Prints a cyan informational message."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def pause():
    """Pauses terminal and prompts user to press Enter."""
    print()
    input(f"{Fore.MAGENTA}Press Enter to continue...{Style.RESET_ALL}")


def format_currency(amount):
    """Formats a number into Indian Rupee format, e.g. ₹10,000."""
    try:
        val = float(amount)
        if val.is_integer():
            return f"₹{int(val):,}"
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{amount}"


def mask_account_number(acc_no):
    """Masks account number: ******452452."""
    acc_str = str(acc_no).strip()
    if len(acc_str) >= 6:
        return f"******{acc_str[-6:]}"
    return f"******{acc_str}"


def mask_phone(phone):
    """Masks phone number keeping last 4 digits visible: ****1234."""
    phone_str = str(phone).strip()
    if len(phone_str) <= 4:
        return f"****{phone_str}"
    return f"****{phone_str[-4:]}"


def get_masked_pin(prompt_text="Enter PIN: "):
    """
    Securely reads PIN input using getpass without echoing to terminal.
    Falls back to normal input if running in a non-interactive pipe or test runner.
    """
    if not sys.stdin.isatty():
        pin = input(prompt_text)
    else:
        try:
            pin = getpass.getpass(prompt_text)
        except Exception:
            pin = input(prompt_text)
    return pin.strip()


def get_safe_int(prompt_text, min_val=None, max_val=None, allow_cancel=False, cancel_value=0):
    """
    Safely prompts user for an integer within an optional range.
    Never crashes on non-numeric input.
    """
    while True:
        try:
            raw = input(prompt_text).strip()
            if allow_cancel and raw == str(cancel_value):
                return cancel_value
            if not raw:
                print_error("Input cannot be empty. Please enter a number.")
                continue
            val = int(raw)
            if min_val is not None and val < min_val:
                print_error(f"Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value cannot exceed {max_val}.")
                continue
            return val
        except ValueError:
            print_error("Invalid input! Please enter a valid whole number.")


def get_safe_float(prompt_text, min_val=None, max_val=None):
    """
    Safely prompts user for a positive float/amount.
    Never crashes on non-numeric input.
    """
    while True:
        try:
            raw = input(prompt_text).strip()
            if not raw:
                print_error("Input cannot be empty. Please enter an amount.")
                continue
            val = float(raw)
            if min_val is not None and val < min_val:
                print_error(f"Amount must be at least {format_currency(min_val)}.")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Amount cannot exceed {format_currency(max_val)}.")
                continue
            return val
        except ValueError:
            print_error("Invalid input! Please enter a valid monetary amount.")


def get_non_empty_string(prompt_text, field_name="Field"):
    """Safely prompts for non-empty text."""
    while True:
        val = input(prompt_text).strip()
        if not val:
            print_error(f"{field_name} cannot be empty.")
            continue
        return val
