# indicators/indicator_bcb.py
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


# ------------------------------------------------------------------------
#   SHORTCUTS (1-liners)
# ------------------------------------------------------------------------

def selic_vs_index_df(df_bcb, df_ibov):
    return bcb_series_vs_index_df(df_bcb, df_ibov, "SELIC")

def ipca_vs_index_df(df_bcb, df_ibov):
    return bcb_series_vs_index_df(df_bcb, df_ibov, "IPCA")

# can add other codes here.
# Testing
