from datetime import datetime

def parse_ddmmyyyy(raw: str, default=None) -> str:
    """
    Convert DDMMYYYY string to YYYY-MM-DD.

    Parameters
    ----------
    raw : str
        A date typed by the user in DDMMYYYY format.
    default : str or None
        If raw is empty and default is provided, return default.

    Returns
    -------
    str
        Date in YYYY-MM-DD format.

    Raises
    ------
    ValueError
        If the format is invalid.
    """
    raw = raw.strip()

    # If the user presses Enter and a default is provided, use it
    if not raw and default:
        return default

    # Will raise ValueError on bad format
    parsed = datetime.strptime(raw, "%d%m%Y")
    return parsed.strftime("%Y-%m-%d")