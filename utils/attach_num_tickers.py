import os
import pandas as pd

def attach_number_tickers(codes_folder: str, market_dict: dict) -> dict:
    """
    For every market whose 'codes_csv' points to a real CSV file,
    open the CSV, count the rows in the 'Code' column, and add:

        'number_tickers': <int>

    Markets with 'codes_csv' == 'none' get number_tickers = 0.

    Returns the modified dictionary.
    """

    for key, info in market_dict.items():

        csv_name = info.get("codes_csv", "none")

        # No ticker list for these items
        if not csv_name or csv_name.lower() == "none":
            info["number_tickers"] = 0
            continue

        # Build full path
        csv_path = os.path.join(codes_folder, csv_name)

        if not os.path.exists(csv_path):
            print(f"Warning: CSV missing: {csv_path}")
            info["number_tickers"] = 0
            continue

        try:
            df = pd.read_csv(csv_path)

            # All your CSVs use column name 'Code'
            if "Code" in df.columns:
                info["number_tickers"] = df["Code"].notna().sum()
            else:
                print(f"Warning: 'Code' column not found in {csv_path}")
                info["number_tickers"] = 0

        except Exception as e:
            print(f"Error reading {csv_path}: {e}")
            info["number_tickers"] = 0

    return market_dict



"""
def count_tickers(obj) -> int:
    
    Count tickers from either:
    1) A CSV file path (counts rows in the file, using 'Codes' column if present)
    2) A pandas DataFrame with MultiIndex columns (counts unique tickers in level 1)

    Parameters
    ----------
    obj : str or pandas.DataFrame
        - str: CSV file path
        - DataFrame: expected to have a MultiIndex on columns: (something, ticker, something)

    Returns
    -------
    int
        Number of tickers found. Returns 0 if unreadable or invalid.
    

    # ======================================================
    # CASE 1 — obj is a CSV file path
    # ======================================================
    if isinstance(obj, str):
        csv_path = obj

        if not csv_path or csv_path.lower() == "none":
            return 0

        if not os.path.exists(csv_path):
            print(f"Warning: ticker file not found: {csv_path}")
            return 0

        try:
            df = pd.read_csv(csv_path)

            # If a "Codes" column exists, count that; else count rows
            if "Code" in df.columns:
                return df["Code"].notna().sum()
            else:
                return len(df)

        except Exception as e:
            print(f"Warning: error reading {csv_path}: {e}")
            return 0


    # ======================================================
    # CASE 2 — obj is a DataFrame with MultiIndex columns
    # ======================================================
    if isinstance(obj, pd.DataFrame):
        cols = obj.columns

        if not isinstance(cols, pd.MultiIndex):
            print("Warning: DataFrame does not have MultiIndex columns.")
            return 0

        if cols.nlevels < 2:
            print("Warning: MultiIndex needs at least 2 levels to extract tickers.")
            return 0

        # Tickers are expected in level 1 (middle level)
        tickers = cols.get_level_values(1)
        unique_tickers = pd.unique(tickers)

        return len(unique_tickers)

    # ======================================================
    # Invalid type
    # ======================================================
    print("Warning: count_tickers() received neither a CSV path nor a DataFrame.")
    return 0
"""
