"""
Highs and Lows Indicator
========================
Calculates rolling high/low breakouts across multiple timeframes:
- ATH/ATL (All-Time High/Low)
- 12MH/12ML (12-month High/Low)
- 3MH/3ML (3-month High/Low)
- 1MH/1ML (1-month High/Low)

Returns aggregated counts and differences across all tickers.
"""

import pandas as pd
from core.my_data_types import PlotSetup


def calculate_highs_and_lows(components_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate highs and lows breakout indicators for all tickers.

    Parameters
    ----------
    df_idx : pd.DataFrame
        Index data with datetime index, must contain 'Adj Close'
    components_df : pd.DataFrame
        EOD data with datetime index, multi-column with 'Adj Close' level

    Returns
    -------
    pd.DataFrame
        Combined DataFrame with columns:
        - ATH, ATL, 12MH, 12ML, 3MH, 3ML, 1MH, 1ML (raw counts)
        - ATH-ATL, 12MH-12ML, 3MH-3ML, 1MH-1ML (net differences)
    """

    close = components_df['Adj Close']  # Extract close prices

    # Calculate rolling max and min for different periods
    rolling_12m_high = close.rolling(window=252).max()
    rolling_12m_low = close.rolling(window=252).min()
    rolling_3m_high = close.rolling(window=63).max()
    rolling_3m_low = close.rolling(window=63).min()
    rolling_1m_high = close.rolling(window=21).max()
    rolling_1m_low = close.rolling(window=21).min()

    # Initialize df2 with 0 values
    df2 = pd.DataFrame(
        0,
        index=close.index,
        columns=pd.MultiIndex.from_product([
            ['ATH', 'ATL', '12MH', '12ML', '3MH', '3ML', '1MH', '1ML'],
            close.columns
        ])
    )

    # Populate df2 based on conditions.  +1 for highs, -1 for lows
    for col in close.columns:
        df2[('ATH', col)] = (close[col] >= close[col].expanding().max()).astype(int)
        df2[('ATL', col)] = -(close[col] <= close[col].expanding().min()).astype(int)
        df2[('12MH', col)] = (close[col] >= rolling_12m_high[col]).astype(int)
        df2[('12ML', col)] = -(close[col] <= rolling_12m_low[col]).astype(int)
        df2[('3MH', col)] = (close[col] >= rolling_3m_high[col]).astype(int)
        df2[('3ML', col)] = -(close[col] <= rolling_3m_low[col]).astype(int)
        df2[('1MH', col)] = (close[col] >= rolling_1m_high[col]).astype(int)
        df2[('1ML', col)] = -(close[col] <= rolling_1m_low[col]).astype(int)

    # Group by level 0 (indicator type) and sum across all tickers
    hl_df = df2.T.groupby(level=0, sort=False).sum().T

    # Creating the High/Low difference DataFrame
    hl_diff_df = pd.DataFrame(index=hl_df.index)
    hl_diff_df['ATH-ATL'] = hl_df['ATH'] + hl_df['ATL']
    hl_diff_df['12MH-12ML'] = hl_df['12MH'] + hl_df['12ML']
    hl_diff_df['3MH-3ML'] = hl_df['3MH'] + hl_df['3ML']
    hl_diff_df['1MH-1ML'] = hl_df['1MH'] + hl_df['1ML']

    # Combine hl_df and hl_diff_df into one DataFrame
    hi_lo = pd.concat([hl_df, hl_diff_df], axis=1)

    return hi_lo


# ============================================================================
# Main for testing
# ============================================================================
if __name__ == "__main__":
    from core.constants import file_locations
    from core.my_data_types import load_file_locations_dict, Config
    from datetime import datetime
    from main_modules.update_or_create import update_or_create_databases
    from utils.align_dataframes import align_and_prepare_for_plot

    # Load file locations
    fileloc = load_file_locations_dict(file_locations)

    # Create test config
    cfg = Config(
        to_do=5,
        market_to_study={13: {'idx_code': '^BVSP', 'market': '3 ticker test',
                              'codes_csv': 'TEST. csv', "number_tickers": 3}},
        to_update={13: {'idx_code': '^BVSP', 'market': '3 ticker test',
                        'codes_csv': 'TEST.csv', "number_tickers": 3}},
        graph_lookback=252,
        yf_start_date="2020-01-01",
        download_end_date=datetime.now().strftime("%Y-%m-%d"),
        yf_end_date=datetime.now().strftime("%Y-%m-%d"),
        study_end_date=None
    )

    # Get data
    index_df, components_df = update_or_create_databases(cfg, fileloc)
    index_df, components_df = align_and_prepare_for_plot(index_df, components_df)

    # Calculate indicator
    hl_result = calculate_highs_and_lows(index_df, components_df)

    print("\n=== Highs and Lows Result ===")
    print(hl_result.tail(10))
    print(f"\nColumns: {hl_result.columns.tolist()}")