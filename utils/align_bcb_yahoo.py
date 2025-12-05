import pandas as pd

def align_bcb_with_yahoo(bcb_monthly: pd.DataFrame,
                         yahoo_df: pd.DataFrame,
                         price_col: str = "Adj Close") -> pd.DataFrame:
    """
    Align BCB monthly data with Yahoo daily data.

    Steps:
    - Ensure both indices are DatetimeIndex.
    - Forward-fill BCB monthly data to daily frequency on yahoo_df's index.
    - Forward-fill any missing values at the end (e.g., last month or two).
    - Return a single daily DataFrame containing:
        - all BCB columns
        - the given Yahoo price column (e.g. Adj Close)
    """
    # Ensure datetime indices
    bcb_monthly = bcb_monthly.copy()
    yahoo_df = yahoo_df.copy()
    bcb_monthly.index = pd.to_datetime(bcb_monthly.index)
    yahoo_df.index = pd.to_datetime(yahoo_df.index)

    # Restrict BCB to a range not beyond Yahoo (optional, can skip)
    start = min(bcb_monthly.index.min(), yahoo_df.index.min())
    end = max(bcb_monthly.index.max(), yahoo_df.index.max())

    # Reindex BCB to daily on the full span you care about (using Yahoo's index)
    # This keeps only days that exist in the Yahoo data (e.g. business days)
    bcb_daily = bcb_monthly.reindex(yahoo_df.index)

    # Forward fill missing values (both for gaps between months and recent months)
    bcb_daily = bcb_daily.ffill()

    # Combine into one DataFrame
    if price_col not in yahoo_df.columns:
        raise KeyError(f"Column '{price_col}' not found in yahoo_df")

    combined = bcb_daily.copy()
    combined[price_col] = yahoo_df[price_col]

    return combined