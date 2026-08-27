import pandas as pd
import numpy as np


def compute_swing_metrics(components_df, index_df):
    """
    Computes Stockbee 4% Expansion, Cumulative Volume A/D, and MA Ratios
    from multi-index components_df (Field, Ticker).
    """
    # Extract Close and Volume DataFrames
    if isinstance(components_df.columns, pd.MultiIndex):
        level_0 = components_df.columns.get_level_values(0)
        if 'Adj Close' in level_0:
            close_df = components_df['Adj Close']
        elif 'Close' in level_0:
            close_df = components_df['Close']
        else:
            close_df = components_df

        if 'Volume' in level_0:
            vol_df = components_df['Volume']
        else:
            vol_df = pd.DataFrame(1, index=close_df.index, columns=close_df.columns)
    else:
        close_df = components_df
        vol_df = pd.DataFrame(1, index=close_df.index, columns=close_df.columns)

    # Daily Returns
    ret_df = close_df.pct_change()

    # 1. Stockbee 4% Expansion
    up_4pct = (ret_df >= 0.04).sum(axis=1)
    down_4pct = (ret_df <= -0.04).sum(axis=1)
    net_4pct = up_4pct - down_4pct

    # 2. Cumulative Volume A/D
    pos_vol = vol_df.where(ret_df > 0, 0).sum(axis=1)
    neg_vol = vol_df.where(ret_df < 0, 0).sum(axis=1)
    cum_vol_ad = (pos_vol - neg_vol).cumsum()

    # 3. MA Ratios (% Stocks Above MAs)
    ma10 = close_df.rolling(10).mean()
    ma50 = close_df.rolling(50).mean()

    above_10ma_pct = (close_df > ma10).mean(axis=1) * 100
    above_50ma_pct = (close_df > ma50).mean(axis=1) * 100

    return {
        "stockbee_up4": up_4pct,
        "stockbee_down4": down_4pct,
        "net_stockbee_4pct": net_4pct,
        "cum_vol_ad": cum_vol_ad,
        "pct_above_10ma": above_10ma_pct,
        "pct_above_50ma": above_50ma_pct
    }