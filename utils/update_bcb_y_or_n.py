def ask_update_bcb() -> bool:
    """
    Ask the user whether to update BCB data.
    Default = No (ENTER returns False).
    Returns True if the user wants to update.
    - Enter → returns False
    - n / N → False
    - y / Y → True
    - Anything else → False
    """
    raw = input("Update BCB data? (y/n) or <Enter> for no): ").strip().lower()

    if raw == "y":
        return True
    return False