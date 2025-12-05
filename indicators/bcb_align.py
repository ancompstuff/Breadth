# indicators/bcb_align.py
import pandas as pd

def _ensure_ibov_adjclose(df_ibov):
    if 'Adj Close' in df_ibov.columns:
        return df_ibov[['Adj Close']].copy()
    # fallback: detect numeric column
    numeric_cols = df_ibov.select_dtypes(include='number').columns
    if len(numeric_cols) >= 1:
        return df_ibov[[numeric_cols[0]]].rename(columns={numeric_cols[0]: 'Adj Close'}).copy()
    raise ValueError("df_ibov must contain 'Adj Close' or at least one numeric column")


def forward_fill_bcb_to_daily(df_bcb, target_index):
    """
    df_bcb: DataFrame (monthly) with columns ['SELIC','IPCA',...]
    target_index: daily IBOV index
    """
    if df_bcb is None:
        return None

    df = df_bcb.copy()
    df.index = pd.to_datetime(df.index, errors='coerce')

    # Forward-fill onto the daily index
    return df.reindex(target_index, method='ffill')


# ------------------------------------------------------------------------
#   GENERIC BUILDER: any BCB column vs IBOV Adj Close
# ------------------------------------------------------------------------

def bcb_series_vs_index_df(df_bcb, df_ibov, column_name):
    """
    Builds a DataFrame with columns ['IBOV', column_name]
    aligned daily (IBOV) with forward-filled BCB (monthly).

    Example:
        bcb_series_vs_index_df(df_bcb, df_ibov, "SELIC")
        bcb_series_vs_index_df(df_bcb, df_ibov, "IPCA")
    """
    if df_bcb is None or df_ibov is None:
        return None

    ibov = _ensure_ibov_adjclose(df_ibov)
    ibov.index = pd.to_datetime(ibov.index, errors='coerce')

    df_bcb_daily = forward_fill_bcb_to_daily(df_bcb, ibov.index)
    if df_bcb_daily is None:
        return None

    if column_name not in df_bcb_daily.columns:
        raise KeyError(f"BCB series '{column_name}' not found in df_bcb")

    return pd.DataFrame({
        'IBOV': ibov['Adj Close'],
        column_name: df_bcb_daily[column_name]
    }, index=ibov.index)


import pandas as pd

# ... existing code ...

def bcb_all_vs_ibov_normalized(df_bcb: pd.DataFrame, df_ibov: pd.DataFrame) -> pd.DataFrame:
    """
    DAILY DataFrame with:
        - 'IBOV' (Adj Close of index)
        - one column per BCB series in df_bcb
    All series:
        - reindexed to IBOV's daily calendar
        - forward-filled (BCB monthly -> daily)
        - normalized to 100 at their first non-NaN value
    """
    if df_bcb is None or df_ibov is None:
        return None

    ibov = _ensure_ibov_adjclose(df_ibov)
    ibov.index = pd.to_datetime(ibov.index, errors='coerce')

    # forward-fill all BCB columns onto IBOV calendar
    df_bcb_daily = forward_fill_bcb_to_daily(df_bcb, ibov.index)
    if df_bcb_daily is None:
        return None

    combined = df_bcb_daily.copy()
    combined["IBOV"] = ibov["Adj Close"]

    # normalise all columns to 100 at first non-NaN
    df_norm = combined.copy()
    for col in df_norm.columns:
        series = df_norm[col].dropna()
        if series.empty:
            df_norm[col] = pd.NA
            continue
        base = series.iloc[0]
        if base == 0 or pd.isna(base):
            df_norm[col] = pd.NA
        else:
            df_norm[col] = (df_norm[col] / base) * 100.0

    df_norm = df_norm.dropna(axis=1, how="all")
    return df_norm


# ------------------------------------------------------------------------
#   SHORTCUTS (1-liners)
# ------------------------------------------------------------------------

def selic_vs_index_df(df_bcb, df_ibov):
    return bcb_series_vs_index_df(df_bcb, df_ibov, "Selic Diária")

def ipca_vs_index_df(df_bcb, df_ibov):
    return bcb_series_vs_index_df(df_bcb, df_ibov, "IPCA")

# can add other codes here.
# Testing
