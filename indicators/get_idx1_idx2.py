# indicators/get_idx1_idx2.py

import os
import pandas as pd
from .bcb_align import selic_vs_index_df, ipca_vs_index_df


def get_idx1_idx2(idx1, idx2, config, fileloc, plot_setup):
    """
    Build a fully aligned dataframe containing:

        IBOV (idx1)  - Adj Close
        IDX2         - Adj Close
        SELIC        - daily forward-filled
        IPCA         - daily forward-filled

    Master timeline = IBOV
    Length = config.graph_lookback
    """

    lookback = int(getattr(config, "graph_lookback", 252))

    # ------------------------------------------------------------
    # 1) Load idx1 from PlotSetup (always provided)
    # ------------------------------------------------------------
    df_idx1 = plot_setup.price_data.copy()
    df_idx1.index = pd.to_datetime(df_idx1.index)
    df_idx1 = df_idx1[['Adj Close']]  # enforce single close column
    df_idx1.columns = ['IBOV']
    df_idx1 = df_idx1.tail(lookback)

    # IBOV defines the master daily timeline
    timeline = df_idx1.index

    # ------------------------------------------------------------
    # 2) Load idx2 from yahoo_downloaded_data_folder
    # ------------------------------------------------------------
    yahoo_folder = fileloc.yahoo_downloaded_data_folder
    f2 = os.path.join(yahoo_folder, f"INDEX_{idx2}.csv")

    if not os.path.exists(f2):
        raise FileNotFoundError(f"idx2 CSV not found: {f2}")

    df_idx2_raw = pd.read_csv(f2, index_col=0, parse_dates=True)
    df_idx2_raw.index = pd.to_datetime(df_idx2_raw.index)

    # pick price column
    if "Adj Close" in df_idx2_raw.columns:
        s2 = df_idx2_raw["Adj Close"]
    else:
        numeric_cols = df_idx2_raw.select_dtypes(include='number').columns
        if len(numeric_cols) == 0:
            raise ValueError(f"No numeric columns in {idx2} CSV.")
        s2 = df_idx2_raw[numeric_cols[0]]

    # align idx2 to IBOV timeline
    s2 = s2.reindex(timeline).ffill()
    df_idx2 = pd.DataFrame({idx2: s2}, index=timeline)

    # ------------------------------------------------------------
    # 3) Load BCB data (monthly) → forward-fill to IBOV daily timeline
    # ------------------------------------------------------------
    bcb_folder = fileloc.bacen_downloaded_data_folder
    bcb_file = os.path.join(bcb_folder, "BCB_IPCA_SELIC.csv")

    if not os.path.exists(bcb_file):
        raise FileNotFoundError(f"BCB file not found: {bcb_file}")

    df_bcb = pd.read_csv(bcb_file, index_col=0, parse_dates=True)
    df_bcb.index = pd.to_datetime(df_bcb.index)

    # daily align SELIC (using helper from bcb_align)
    df_selic = selic_vs_index_df(df_bcb, df_idx1)
    df_selic = df_selic[['SELIC']].reindex(timeline).ffill()

    # daily align IPCA
    df_ipca = ipca_vs_index_df(df_bcb, df_idx1)
    df_ipca = df_ipca[['IPCA']].reindex(timeline).ffill()

    # ------------------------------------------------------------
    # 4) Merge all into one daily dataframe aligned to IBOV
    # ------------------------------------------------------------
    df = pd.concat([df_idx1, df_idx2, df_selic, df_ipca], axis=1)

    # ensure no NA remains
    #df = df.fillna(method="ffill").fillna(method="bfill")  # gives future warning
    df = df.ffill().bfill()

    # MUST be same length as lookback
    assert len(df) == lookback, f"Final df length {len(df)} != lookback {lookback}"

    return df
