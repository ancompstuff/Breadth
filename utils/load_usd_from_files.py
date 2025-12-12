import os
import pandas as pd

def load_usd_series(fileloc):
    """
    Load USD (BRL=X) from the local Yahoo download folder.
    Returns a pandas Series indexed by date.
    """
    fname = os.path.join(
        fileloc.yahoo_downloaded_data_folder,
        "INDEX_BRL=X.csv"
    )

    if not os.path.exists(fname):
        raise FileNotFoundError(f"USD file not found: {fname}")

    df = pd.read_csv(fname, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)

    # choose best column
    if "Adj Close" in df.columns:
        s = df["Adj Close"]
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        if len(numeric_cols) == 0:
            raise ValueError(f"No numeric numeric columns in USD file: {fname}")
        s = df[numeric_cols[0]]

    s.name = "BRL=X"
    return s
