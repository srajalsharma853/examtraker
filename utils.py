"""
utils.py
--------
Reusable input-validation and display helpers, so the same
"keep asking until valid" logic is not repeated across the program.
"""

from datetime import date, datetime


def print_header(title):
    """Print a consistent section header."""
    print("\n" + "=" * 50)
    print(title.center(50))
    print("=" * 50)


def pause():
    """Wait for Enter so the user can read the output."""
    input("\nPress Enter to continue...")


def today():
    """Return today's date (kept in one place for easy testing)."""
    return date.today()


def get_non_empty_string(prompt):
    """Keep asking until the user types something non-empty."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty. Please try again.")


def get_menu_choice(prompt, valid_choices):
    """Keep asking until the input is one of the valid menu options."""
    while True:
        raw = input(prompt).strip()
        if raw in valid_choices:
            return raw
        print("Invalid menu choice. Please try again.")


def get_yes_no(prompt):
    """Ask a yes/no question. Returns True for yes, False for no."""
    while True:
        raw = input(prompt + " (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")


def get_choice_from_list(prompt, options):
    """Ask for one option from a list (case-insensitive). Returns the proper spelling."""
    shown = "/".join(options)
    while True:
        raw = input(f"{prompt} ({shown}): ").strip().lower()
        for option in options:
            if raw == option.lower():
                return option
        print(f"Invalid choice. Please choose one of: {shown}")


def get_future_date(prompt):
    """
    Ask for a date as YYYY-MM-DD. Keeps asking until it is a real calendar
    date that is today or later (an exam date in the past makes no sense).
    Returns a date object.
    """
    while True:
        raw = input(prompt + " (YYYY-MM-DD): ").strip()
        try:
            chosen = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("That is not a valid date. Example: 2026-11-20")
            continue
        if chosen < today():
            print("The date cannot be in the past.")
            continue
        return chosen