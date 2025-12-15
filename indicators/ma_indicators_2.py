from typing import List, Tuple, Optional, Any
import pandas as pd

from core.constants import mas_list, trend_combinations
from core.my_data_types import Config, PlotSetup


def calculate_trend_combinations(df_eod_with_mas_vwmas: pd.DataFrame,
                                 plot_setup: PlotSetup) -> pd.DataFrame:
    """
    Calculate trend combinations based on VWMA values.

    Counts how many tickers are above specific VWMA combinations:
    - Short: VWMA5, VWMA5&12, VWMA5&12&25
    - Medium: VWMA40, VWMA40&60, VWMA40&60&80
    - Long: VWMA50, VWMA50&100, VWMA50&100&200

    Parameters
    ----------
    df_eod_with_mas_vwmas : pd.DataFrame
        DataFrame with individual ticker data including VWMA columns
    plot_setup : PlotSetup
        Contains num_tickers for normalization

    Returns
    -------
    pd.DataFrame
        DataFrame with trend combination counts
    """

    close_eod = df_eod_with_mas_vwmas['Adj Close']
    num_tickers = plot_setup.num_tickers

    # Create dictionary to store results
    trends = {}

    # Calculate for each combination
    for trend_name, vwma_list in trend_combinations.items():
        # Start with all True
        mask = pd.Series(True, index=close_eod.index)

        for vwma in vwma_list:
            if vwma in df_eod_with_mas_vwmas.columns:
                # Check if price is above this VWMA
                above_mask = close_eod > df_eod_with_mas_vwmas[vwma]
                mask = mask & above_mask
            else:
                print(f"Warning: {vwma} not found in dataframe columns")
                mask = pd.Series(False, index=close_eod.index)
                break

        # Count tickers where all conditions are True
        count_series = mask.sum(axis=1)
        trends[f"Nº>{trend_name}"] = count_series
        trends[f"%>{trend_name}"] = (count_series / num_tickers) * 100

    # Create DataFrame from trends dictionary
    df_trends = pd.DataFrame(trends, index=close_eod.index)

    return df_trends


# Also, update the existing function to create the combined trends dataframe
def create_trends_dataframe(df_idx_with_mas_vwmas: pd.DataFrame,
                            df_eod_with_mas_vwmas: pd.DataFrame,
                            plot_setup: PlotSetup) -> pd.DataFrame:
    """
    Create comprehensive trends dataframe with price, basic counts, and combination counts.

    Returns dataframe with:
    1) Adj Close from df_idx_with_mas_vwmas
    2) Nº>VWMA5, Nº>VWMA40, Nº>VWMA50 (from existing calculation)
    3) Trend combination counts
    """

    # First get the basic counts (this should already exist)
    # We need to extract Nº>VWMA5, Nº>VWMA40, Nº>VWMA50 from df_idx_num_percent_above_below_mas_vwmas
    # For now, let's calculate them directly:

    close_eod = df_eod_with_mas_vwmas['Adj Close']
    num_tickers = plot_setup.num_tickers

    # Calculate basic single VWMA counts
    basic_counts = {}
    for ma in [5, 40, 50]:  # Only the ones we need for the trends dataframe
        vwma_col = f"VWMA{ma}"
        if vwma_col in df_eod_with_mas_vwmas.columns:
            mask = close_eod > df_eod_with_mas_vwmas[vwma_col]
            count_series = mask.sum(axis=1)
            basic_counts[f"Nº>{vwma_col}"] = count_series
            basic_counts[f"%>{vwma_col}"] = (count_series / num_tickers) * 100

    # Calculate trend combinations
    df_trend_combinations = calculate_trend_combinations(df_eod_with_mas_vwmas, plot_setup)

    # Start building the final dataframe
    df_final = pd.DataFrame(index=df_idx_with_mas_vwmas.index)

    # 1) Add Adj Close
    if 'Adj Close' in df_idx_with_mas_vwmas.columns:
        df_final['Adj Close'] = df_idx_with_mas_vwmas['Adj Close']

    # 2) Add basic counts from dictionary
    for col_name, series in basic_counts.items():
        df_final[col_name] = series

    # 3) Add trend combinations
    for col in df_trend_combinations.columns:
        df_final[col] = df_trend_combinations[col]

    # Also add some useful derived columns
    # Calculate percentages for the combination trends if not already there
    for col in df_final.columns:
        if col.startswith('Nº>') and f"%{col[2:]}" not in df_final.columns:
            percent_col = f"%{col[2:]}"
            if percent_col in df_final.columns:
                # Already calculated
                continue
            # Calculate percentage
            df_final[percent_col] = (df_final[col] / num_tickers) * 100

    return df_final


# Alternative: Integrate with existing calculate_tickers_over_under_mas function
def calculate_tickers_over_under_mas_with_trends(df_idx_with_mas_vwmas: pd.DataFrame,
                                                 df_eod_with_mas_vwmas: pd.DataFrame,
                                                 plot_setup: PlotSetup) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Enhanced version that returns both the basic counts and trend combinations.

    Returns:
    - df_idx_num_percent_above_below_mas_vwmas: Original counts for all MAs
    - df_trends: Trend combination dataframe
    """

    # Get original counts (your existing function)
    df_basic_counts = calculate_tickers_over_under_mas(df_idx_with_mas_vwmas, df_eod_with_mas_vwmas, plot_setup)

    # Get trend combinations
    df_trends = create_trends_dataframe(df_idx_with_mas_vwmas, df_eod_with_mas_vwmas, plot_setup)

    return df_basic_counts, df_trends
