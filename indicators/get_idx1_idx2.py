import os
import pandas as pd

from indicators.indicator_bcb import selic_vs_index_df, ipca_vs_index_df


def get_idx_idx2(idx1, idx2, ps, fileloc, lookback=252):
    """
    Prepare a merged DataFrame containing:

    - Adj Close of idx1 (taken from PlotSetup)
    - Adj Close of idx2 (loaded from CSV)
    - SELIC (aligned, forward-filled)
    - IPCA (aligned, forward-filled)

    All aligned to idx1's date index and trimmed to lookback rows.
    """

    # ---------------------------------------------------------
    # 1) IBOV / idx1 from PlotSetup
    # ---------------------------------------------------------
    df1 = ps.price_data.copy()
    df1 = df1.tail(lookback)

    if "Adj Close" in df1.columns:
        col1 = "Adj Close"
    elif "Close" in df1.columns:
        col1 = "Close"
    else:
        col1 = df1.select_dtypes("number").columns[0]

    df_out = pd.DataFrame(index=df1.index)
    df_out[f"{idx1}_Close"] = df1[col1]

    # ---------------------------------------------------------
    # 2) Load idx2 from CSV
    # ---------------------------------------------------------
    csv_folder = fileloc.downloaded_data_folder
    idx2_path = os.path.join(csv_folder, f"INDEX_{idx2}.csv")

    if not os.path.exists(idx2_path):
        raise RuntimeError(f"File not found: {idx2_path}")

    df2 = pd.read_csv(idx2_path, index_col=0, parse_dates=True)

    # align to idx1 dates
    df2 = df2.loc[df_out.index]

    if "Adj Close" in df2.columns:
        col2 = "Adj Close"
    elif "Close" in df2.columns:
        col2 = "Close"
    else:
        col2 = df2.select_dtypes("number").columns[0]

    df_out[f"{idx2}_Close"] = df2[col2]

    # ---------------------------------------------------------
    # 3) Load SELIC/IPCA
    # ---------------------------------------------------------
    bcb_path = os.path.join(csv_folder, "bcb", "BCB_IPCA_SELIC.csv")

    if not os.path.exists(bcb_path):
        raise RuntimeError(f"Missing BCB file: {bcb_path}")

    df_bcb = pd.read_csv(bcb_path, index_col=0, parse_dates=True)

    df_selic = selic_vs_index_df(df_bcb, df_out)
    df_ipca = ipca_vs_index_df(df_bcb, df_out)

    df_out["SELIC"] = df_selic["SELIC"]
    df_out["IPCA"] = df_ipca["IPCA"]

    # ---------------------------------------------------------
    # 4) Return a single, clean dataframe
    # ---------------------------------------------------------
    return df_out
