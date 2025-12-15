import pandas as pd


#################################################################################################
def align_and_prepare_for_plot(df1: pd.DataFrame, df2: pd.DataFrame, verbose: bool = True):
    """
    Aligns two DataFrames (typically one index and one market dataset) by their common datetime index
    to ensure both are compatible for time series analysis or plotting.

    Parameters:
    -----------
    df1 : pd.DataFrame
        First DataFrame (commonly an index like S&P500, Nasdaq, etc.). Must have a datetime index.
    df2 : pd.DataFrame
        Second DataFrame (typically end-of-day price data for multiple tickers). Must have a datetime index.
    verbose : bool, optional (default=True)
        If True, prints summary info on date alignment and number of common dates.

    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame]
        A tuple containing the two input DataFrames filtered to contain only common dates,
        both sorted by date.

    Raises:
    -------
    ValueError
        If no common dates are found between the two DataFrames.

    Notes:
    ------
    - This function assumes both inputs are already preprocessed and indexed by date.
    - The function is useful for ensuring synchronized timeframes before plotting overlays
      or performing time series operations (e.g., correlation, rolling stats).
    """
#################################################################################################

    # Step 1: Ensure datetime index
    df2.index = pd.to_datetime(df2.index)
    df1.index = pd.to_datetime(df1.index)
    if not df1.index.is_unique or not df2.index.is_unique:
        raise ValueError("Indices must be unique for direct date alignment.")

    # Step 2: Find common trading dates (intersection)
    common_dates = df2.index.intersection(df1.index).sort_values()

    if verbose:
        print(f"[INFO] df_eod dates: {len(df2.index)}")
        print(f"[INFO] df_idx dates: {len(df1.index)}")
        print(f"[INFO] Common trading dates: {len(common_dates)}")

    if len(common_dates) == 0:
        raise ValueError("No common trading dates found between df_eod and df_idx.")

    # Step 3: Filter both to those dates (direct indexing is much faster than isin)
    df2 = df2.loc[common_dates]
    df1 = df1.loc[common_dates]

    return df1, df2
