import pandas as pd
import numpy as np
import talib


def calculate_advance_decline(df_idx: pd.DataFrame, df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate advance/decline indicators including TRIN, cumulative A/D, and McClellan Oscillator.

    Args:
        df_idx: Index DataFrame with 'Adj Close' column
        df_comp:  EOD DataFrame with MultiIndex columns containing 'Adj Close' and 'Volume'

    Returns:
        DataFrame with advance/decline indicators indexed by date
    """
    # Number of tickers
    num_stocks = df_comp.columns.get_level_values(1).nunique()

    # Get daily price changes
    price_change = df_comp['Adj Close'].diff()
    price_direction = np.sign(price_change)

    # Count advancing / declining issues
    advancing_stocks = (price_direction == 1).sum(axis=1)
    declining_stocks = (price_direction == -1).sum(axis=1)

    # Get volumes
    volume = df_comp['Volume']

    # Mask for advancing and declining volumes
    advancing_volume = volume.where(price_direction == 1).sum(axis=1)
    declining_volume = volume.where(price_direction == -1).sum(axis=1)

    # Avoid division by zero for TRIN calculation
    adv_issues = advancing_stocks.replace(0, np.nan)
    dec_issues = declining_stocks.replace(0, np.nan)
    adv_vol = advancing_volume.replace(0, np.nan)
    dec_vol = declining_volume.replace(0, np.nan)

    # Calculate TRIN
    trin = (adv_issues / dec_issues) / (adv_vol / dec_vol)
    trin = trin.rename("TRIN")
    # TRIN becomes NaN on any day where any part of the ratio is undefined. No declining or advancing stock/vol.


    # Build main indicators dataframe
    adv_dec_indicators = pd.DataFrame({
        'Advancing': advancing_stocks,
        'Declining': declining_stocks,
        'TRIN': trin,
        'idx_close': df_idx['Adj Close']
    })

    # Calculate A/D difference and cumulative
    adv_dec_diff = (advancing_stocks - declining_stocks).rename("A/D_diff")
    adv_dec_cum_diff = adv_dec_diff.cumsum().rename("A/D_cum_diff")

    adv_dec_indicators['A/D_diff'] = adv_dec_diff
    adv_dec_indicators['A/D_cum_diff'] = adv_dec_cum_diff

    # Calculate EMAs for McClellan Oscillator using TA-Lib
    adv = adv_dec_indicators['Advancing'].fillna(0).astype('float64').values
    dec = adv_dec_indicators['Declining'].fillna(0).astype('float64').values
    diff = adv_dec_indicators['A/D_diff'].fillna(0).astype('float64').values

    adv_dec_indicators['Advancing_EMA_19'] = talib.EMA(adv, timeperiod=19)
    adv_dec_indicators['Advancing_EMA_39'] = talib.EMA(adv, timeperiod=39)
    adv_dec_indicators['Declining_EMA_19'] = talib.EMA(dec, timeperiod=19)
    adv_dec_indicators['Declining_EMA_39'] = talib.EMA(dec, timeperiod=39)
    adv_dec_indicators['A/D_diff_EMA_19'] = talib.EMA(diff, timeperiod=19)
    adv_dec_indicators['A/D_diff_EMA_39'] = talib.EMA(diff, timeperiod=39)

    # Calculate McClellan Oscillator
    adv_dec_indicators['McClellan_Oscillator'] = (
            adv_dec_indicators['A/D_diff_EMA_19'] - adv_dec_indicators['A/D_diff_EMA_39']
    )

    return adv_dec_indicators