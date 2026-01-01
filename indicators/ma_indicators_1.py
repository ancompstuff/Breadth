
from typing import List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from pathlib import Path
from tabulate import tabulate
import itertools

# Project constants (assumed present in your project)
import core.constants
from core.my_data_types import Config, PlotSetup
from utils import zscore as zsc


# ---------------------------
# Calculate MAs e VWMAs
# ---------------------------
def calculate_idx_and_comp_ma_vwma(df_idx: pd.DataFrame,
                                   df_eod: pd.DataFrame)\
        -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate MA and VWMA series for index and each ticker.

    Returns tuple (df_idx_with_mas_vwmas, df_eod_with_mas_vwmas).
    """
    # Index MAs / VWMAs
    close = df_idx['Adj Close']
    volume = df_idx['Volume']

    results = {}
    for ma in core.constants.mas_list:
        results[f"MA{ma}"] = close.rolling(window=ma).mean()
        # volume-weighted moving average
        vwma = (close * volume).rolling(window=ma).sum() / volume.rolling(window=ma).sum()
        results[f"VWMA{ma}"] = vwma

    df_idx_with_mas_vwmas = pd.concat([df_idx, pd.DataFrame(results)], axis=1)

    # EOD (tickers) MAs / VWMAs
    close_eod = df_eod['Adj Close']
    vol_eod = df_eod['Volume']

    eod_frames = []
    for ma in core.constants.mas_list:
        sma_df = close_eod.rolling(window=ma).mean()
        vwma_df = (close_eod * vol_eod).rolling(window=ma).sum() / vol_eod.rolling(window=ma).sum()
        eod_frames.append((f"MA{ma}", sma_df))
        eod_frames.append((f"VWMA{ma}", vwma_df))

    df_eod_with_mas_vwmas = pd.concat([frame for _, frame in eod_frames], axis=1, keys=[label for label, _ in eod_frames])
    # Prepend original Adj Close and Volume
    df_eod_with_mas_vwmas = pd.concat([df_eod[['Adj Close', 'Volume']], df_eod_with_mas_vwmas], axis=1)

    return df_idx_with_mas_vwmas, df_eod_with_mas_vwmas


# --------------------------------------------------
# MA convergence/divergence oscillator
# measures how tightly or widely spread MAs are
# indicating market compression or expansion phases
# --------------------------------------------------
def calc_conver_diver_oscillator(
        df_idx_with_mas_vwmas: pd.DataFrame,
        plot_setup: PlotSetup,
        oscillator_type: str = 'zscore',
        zscore_mode: str = 'swing',  # "swing", "longterm", "anomalies"
        oscillator_lookback: str = 'osc_lookback',  # ignored for zscore, used for minmax
) -> pd.DataFrame:
    """
    Compute MA/VWMA ranges, normalize by price, and produce an oscillator.

    Parameters:
    -----------
    oscillator_type : {'minmax', 'zscore'}
        Oscillator normalization method.
    zscore_mode : {'swing', 'longterm', 'anomalies'}
        Mode for rolling_robust_zscore from core.constants.zscore_params.
    """
    df_result = df_idx_with_mas_vwmas.copy()

    # Get short-term periods
    short_periods = core.constants.ma_groups['short']['periods']

    # Column selection (unchanged for full and no200)
    ma_cols = [c for c in df_result.columns if
               isinstance(c, str) and c.startswith('MA') and not c.startswith(('MA_', 'VWMA_'))]
    vwma_cols = [c for c in df_result.columns if
                 isinstance(c, str) and c.startswith('VWMA') and not c.startswith(('MA_', 'VWMA_'))]
    ma_cols_no200 = [c for c in ma_cols if not c.endswith('200')]
    vwma_cols_no200 = [c for c in vwma_cols if not c.endswith('200')]

    # New: Short-term columns (only for periods in short_periods)
    short_ma_cols = [c for c in ma_cols if any(c.endswith(str(ma)) for ma in short_periods)]
    short_vwma_cols = [c for c in vwma_cols if any(c.endswith(str(ma)) for ma in short_periods)]

    range_configs = [
        {'cols': ma_cols, 'prefix': 'MA'},
        {'cols': ma_cols_no200, 'prefix': 'MA_no200'},
        {'cols': vwma_cols, 'prefix': 'VWMA'},
        {'cols': vwma_cols_no200, 'prefix': 'VWMA_no200'},
        # New: Short-term configs
        {'cols': short_ma_cols, 'prefix': 'short_MA'},
        {'cols': short_vwma_cols, 'prefix': 'short_VWMA'}
    ]
    for cfg in range_configs:
        if cfg['cols']:
            df_result[f"{cfg['prefix']}_max"] = df_result[cfg['cols']].max(axis=1)
            df_result[f"{cfg['prefix']}_min"] = df_result[cfg['cols']].min(axis=1)
            df_result[f"{cfg['prefix']}_range"] = df_result[f"{cfg['prefix']}_max"] - df_result[f"{cfg['prefix']}_min"]

    # Normalize by price
    eps = 1e-9
    if 'Adj Close' not in df_result.columns:
        raise KeyError("df_idx_with_mas_vwmas must contain 'Adj Close' for normalization")
    price = df_result['Adj Close']
    df_result['MA_no200_range_pct'] = df_result['MA_no200_range'] / (price + eps)
    df_result['VWMA_no200_range_pct'] = df_result['VWMA_no200_range'] / (price + eps)
    # New: Short-term normalizations
    df_result['short_MA_range_pct'] = df_result['short_MA_range'] / (price + eps)
    df_result['short_VWMA_range_pct'] = df_result['short_VWMA_range'] / (price + eps)

    # ---------------------------------------------------------------------------------------------
    # Create oscillator
    # ---------------------------------------------------------------------------------------------
    if oscillator_type == 'minmax':
    # ---------------------------------------------------------------------------------------------
        lookback = oscillator_lookback
        roll_min_ma = df_result['MA_no200_range_pct'].rolling(window=lookback, min_periods=1).min()
        roll_max_ma = df_result['MA_no200_range_pct'].rolling(window=lookback, min_periods=1).max()
        denom_ma = (roll_max_ma - roll_min_ma).replace(0, np.nan)
        df_result['MA_no200_osc'] = (
            ((df_result['MA_no200_range_pct'] - roll_min_ma) / denom_ma).clip(0.0,1.0).fillna(0.0))

        roll_min_v = df_result['VWMA_no200_range_pct'].rolling(window=lookback, min_periods=1).min()
        roll_max_v = df_result['VWMA_no200_range_pct'].rolling(window=lookback, min_periods=1).max()
        denom_v = (roll_max_v - roll_min_v).replace(0, np.nan)
        df_result['VWMA_no200_osc'] = (
            ((df_result['VWMA_no200_range_pct'] - roll_min_v) / denom_v).clip(0.0, 1.0).fillna(0.0))

        # New: Short-term oscillators for minmax
        roll_min_short_ma = df_result['short_MA_range_pct'].rolling(window=lookback, min_periods=1).min()
        roll_max_short_ma = df_result['short_MA_range_pct'].rolling(window=lookback, min_periods=1).max()
        denom_short_ma = (roll_max_short_ma - roll_min_short_ma).replace(0, np.nan)
        df_result['short_MA_osc'] = (
            ((df_result['short_MA_range_pct'] - roll_min_short_ma) / denom_short_ma).clip(0.0, 1.0).fillna(0.0))

        roll_min_short_v = df_result['short_VWMA_range_pct'].rolling(window=lookback, min_periods=1).min()
        roll_max_short_v = df_result['short_VWMA_range_pct'].rolling(window=lookback, min_periods=1).max()
        denom_short_v = (roll_max_short_v - roll_min_short_v).replace(0, np.nan)
        df_result['short_VWMA_osc'] = (
            ((df_result['short_VWMA_range_pct'] - roll_min_short_v) / denom_short_v).clip(0.0, 1.0).fillna(0.0))

    # ---------------------------------------------------------------------------------------------
    elif oscillator_type == 'zscore':
    # ---------------------------------------------------------------------------------------------
        # Use your rolling_robust_zscore with configurable mode
        df_result['MA_no200_osc'] = zsc.rolling_robust_zscore(
            df_result['MA_no200_range_pct'],
            mode=zscore_mode
        )
        df_result['VWMA_no200_osc'] = zsc.rolling_robust_zscore(
            df_result['VWMA_no200_range_pct'],
            mode=zscore_mode,
            score_params=core.constants.zscore_params  # pass explicitly if needed
        )
        # New: Short-term oscillators for zscore
        df_result['short_MA_osc'] = zsc.rolling_robust_zscore(
            df_result['short_MA_range_pct'],
            mode=zscore_mode
        )
        df_result['short_VWMA_osc'] = zsc.rolling_robust_zscore(
            df_result['short_VWMA_range_pct'],
            mode=zscore_mode,
            score_params=core.constants.zscore_params
        )
    else:
        raise ValueError("oscillator_type must be 'minmax' or 'zscore'")
    # ---------------------------------------------------------------------------------------------

    """ # Scale oscillator for plotting (20% of plot height)
    scale = 0.2 * (plot_setup.ymax - plot_setup.ymin) if (plot_setup.ymax - plot_setup.ymin) != 0 else 1.0
    offset = plot_setup.ymin
    df_result['VWMA_no200_osc_scaled'] = df_result['VWMA_no200_osc'] * scale + offset
    # New: Short-term scaled oscillator
    df_result['short_VWMA_osc_scaled'] = df_result['short_VWMA_osc'] * scale + offset"""

    return df_result


def calculate_tickers_over_under_mas(
    df_idx_with_mas_vwmas: pd.DataFrame,
    df_eod_with_mas_vwmas: pd.DataFrame,
    plot_setup: PlotSetup,
    neutral_band_pct: float = 0.005,   # 0.5% neutral band
    smooth_window: int = 3,            # days for SMA smoothing of breadth
) -> pd.DataFrame:
    """
    Count how many tickers are above/below each MA/VWMA and return a DataFrame
    of aggregated index-level stats, using a neutral band around MAs.

        For each MA period (e.g., MA20):
    1. % Above MA20         → Stocks in clear uptrend relative to MA20
    2. % Below MA20         → Stocks in clear downtrend relative to MA20
    3. % Neutral (≈) MA20   → Stocks consolidating near MA20

    """
    num_tickers = plot_setup.num_tickers

    close_eod = df_eod_with_mas_vwmas['Adj Close']

    combined_frames = []

    for ma in core.constants.mas_list:
        sma_df = df_eod_with_mas_vwmas[f"MA{ma}"]
        vwma_df = df_eod_with_mas_vwmas[f"VWMA{ma}"]

        # percentage diff from MA/VWMA
        eps = 1e-9
        pct_diff_ma = (close_eod - sma_df) / (close_eod + eps)
        pct_diff_vwma = (close_eod - vwma_df) / (close_eod + eps)

        # classify with neutral band: -1 below, 0 neutral, +1 above
        ma_comp_df = pd.DataFrame(index=pct_diff_ma.index, columns=pct_diff_ma.columns)
        ma_comp_df[pct_diff_ma > neutral_band_pct] = 1
        ma_comp_df[pct_diff_ma < -neutral_band_pct] = -1
        ma_comp_df = ma_comp_df.apply(pd.to_numeric, errors="coerce").fillna(0)

        vwma_comp_df = pd.DataFrame(index=pct_diff_vwma.index, columns=pct_diff_vwma.columns)
        vwma_comp_df[pct_diff_vwma > neutral_band_pct] = 1
        vwma_comp_df[pct_diff_vwma < -neutral_band_pct] = -1
        vwma_comp_df = vwma_comp_df.apply(pd.to_numeric, errors="coerce").fillna(0)

        # aggregate across tickers
        num_above_ma = (ma_comp_df == 1).sum(axis=1)
        num_below_ma = (ma_comp_df == -1).sum(axis=1)
        num_neutral_ma = (ma_comp_df == 0).sum(axis=1)

        num_above_vwma = (vwma_comp_df == 1).sum(axis=1)
        num_below_vwma = (vwma_comp_df == -1).sum(axis=1)
        num_neutral_vwma = (vwma_comp_df == 0).sum(axis=1)

        pct_above_ma = num_above_ma / num_tickers * 100.0
        pct_below_ma = num_below_ma / num_tickers * 100.0
        pct_neutral_ma = num_neutral_ma / num_tickers * 100.0

        pct_above_vwma = num_above_vwma / num_tickers * 100.0
        pct_below_vwma = num_below_vwma / num_tickers * 100.0
        pct_neutral_vwma = num_neutral_vwma / num_tickers * 100.0

        # optional smoothing (simple MA)
        if smooth_window and smooth_window > 1:
            pct_above_ma = pct_above_ma.rolling(window=smooth_window, min_periods=1).mean()
            pct_below_ma = pct_below_ma.rolling(window=smooth_window, min_periods=1).mean()
            pct_neutral_ma = pct_neutral_ma.rolling(window=smooth_window, min_periods=1).mean()

            pct_above_vwma = pct_above_vwma.rolling(window=smooth_window, min_periods=1).mean()
            pct_below_vwma = pct_below_vwma.rolling(window=smooth_window, min_periods=1).mean()
            pct_neutral_vwma = pct_neutral_vwma.rolling(window=smooth_window, min_periods=1).mean()

        label = f"MA{ma}"
        vlabel = f"VWMA{ma}"

        combined = pd.DataFrame(index=df_idx_with_mas_vwmas.index)
        combined[f"Nº>{label}"] = num_above_ma
        combined[f"Nº<{label}"] = num_below_ma
        combined[f"Nº≈{label}"] = num_neutral_ma
        combined[f"%>{label}"] = pct_above_ma
        combined[f"%<{label}"] = pct_below_ma
        combined[f"%≈{label}"] = pct_neutral_ma

        combined[f"Nº>{vlabel}"] = num_above_vwma
        combined[f"Nº<{vlabel}"] = num_below_vwma
        combined[f"Nº≈{vlabel}"] = num_neutral_vwma
        combined[f"%>{vlabel}"] = pct_above_vwma
        combined[f"%<{vlabel}"] = pct_below_vwma
        combined[f"%≈{vlabel}"] = pct_neutral_vwma

        combined_frames.append(combined)

    df_idx_num_percent_above_below_mas_vwmas = pd.concat(combined_frames, axis=1)
    return df_idx_num_percent_above_below_mas_vwmas



def calculate_compressao_dispersao(df_idx_with_mas_vwmas: pd.DataFrame,
                                    df_eod_with_mas_vwmas: pd.DataFrame
                                    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dispersion analysis engine
    measures how far individual stocks are from their moving averages
    quantifies market "alignment" or "dislocation."

    Compute compression/dispersion metrics at index and ticker levels.

    Returns (df_idx_compression, df_eod_compression).
    """
    df_idx_compression = df_idx_with_mas_vwmas.copy()
    df_eod_compression = df_eod_with_mas_vwmas.copy()

    close_eod = df_eod_compression['Adj Close']

    for ma in core.constants.mas_list:
        # Create a % diff between price and MA
        diff_ma_df = (close_eod - df_eod_compression[f"MA{ma}"]) / close_eod
        diff_vwma_df = (close_eod - df_eod_compression[f"VWMA{ma}"]) / close_eod

        # Aggregate across all tickers. Absolute Compression (ignores direction)
        abs_comp_ma = diff_ma_df.abs().sum(axis=1)
        abs_comp_vwma = diff_vwma_df.abs().sum(axis=1)
        # Aggregate across all tickers. Takes into account direction.
        dir_comp_ma = diff_ma_df.sum(axis=1)
        dir_comp_vwma = diff_vwma_df.sum(axis=1)

        diff_ma_df.columns = pd.MultiIndex.from_product([[f"C-MA{ma}"], diff_ma_df.columns])
        diff_vwma_df.columns = pd.MultiIndex.from_product([[f"C-VWMA{ma}"], diff_vwma_df.columns])

        df_eod_compression = pd.concat([df_eod_compression, diff_ma_df, diff_vwma_df], axis=1)

        df_idx_compression[f"Abs_C-MA{ma}"] = abs_comp_ma
        df_idx_compression[f"Abs_C-VWMA{ma}"] = abs_comp_vwma
        df_idx_compression[f"Dir_C-MA{ma}"] = dir_comp_ma
        df_idx_compression[f"Dir_C-VWMA{ma}"] = dir_comp_vwma

    # Aggregate by groups defined in core.constants.ma_groups
    for group_name, ma_group in core.constants.ma_groups.items():
        periods_list = ma_group.get("periods", [])
        abs_cols = [f"Abs_C-VWMA{ma}" for ma in periods_list if f"Abs_C-VWMA{ma}" in df_idx_compression.columns]
        dir_cols = [f"Dir_C-VWMA{ma}" for ma in periods_list if f"Dir_C-VWMA{ma}" in df_idx_compression.columns]

        if abs_cols:
            df_idx_compression[f"Abs_VWMA_{group_name}_sum"] = df_idx_compression[abs_cols].sum(axis=1)
        if dir_cols:
            df_idx_compression[f"Dir_VWMA_{group_name}_sum"] = df_idx_compression[dir_cols].sum(axis=1)

    return df_idx_compression, df_eod_compression


#################################################################################################################
# ----------------------------------------------- TEST ----------------------------------------------------------
#################################################################################################################
if __name__ == "__main__":
    print(f"{'=' * 30}\nTESTING MODULE: ma_indicators_1\n{'=' * 30}")

    def print_df_summary(name: str, df: pd.DataFrame):
        print(f"\n>>> DATAFRAME: {name}")
        print(f"    Shape: {df.shape}")
        print(f"    Columns ({len(df.columns)}):")
        # Handle MultiIndex and standard columns for readability
        cols = [str(c) for c in df.columns.tolist()]
        if len(cols) > 10:
            print(f"      {cols[:5]} ... {cols[-5:]}")
        else:
            print(f"      {cols}")


    # Get the path to the current script, go to its parent, then up again to the root
    # then look for the data_cache folder
    data_dir = Path(__file__).resolve().parent.parent / "data_cache"

    index_path = data_dir / "index_df.parquet"
    comp_path = data_dir / "components_df.parquet"

    # Load the data
    df_idx = pd.read_parquet(index_path)
    df_comp = pd.read_parquet(comp_path)

    print(f"Successfully loaded Index data with {len(df_idx)} rows.")

    # FUNCTION TO TEST
    df_idx_mas, df_comp_mas = calculate_idx_and_comp_ma_vwma(df_idx, df_comp)

    print_df_summary("Index (with MAs/VWMAs)", df_idx_mas)
    print_df_summary("EOD (with MAs/VWMAs)", df_comp_mas)

    # 1. Extract the unique Level 0 labels
    # df_idx_mas is single level, so unique() is straightforward
    idx_labels = df_idx_mas.columns.unique().tolist()

    # df_comp_mas is MultiIndex; we only want the top categories (indicators)
    comp_labels = df_comp_mas.columns.get_level_values(0).unique().tolist()

    # 2. Align the lists for a side-by-side table
    # We use zip_longest to handle lists of different lengths

    table_data = list(itertools.zip_longest(idx_labels, comp_labels, fillvalue=""))

    # 3. Print the formatted table
    print("\n>>> Comparison of Level 0 Column Labels")
    print(tabulate(
        table_data,
        headers=["df_idx_mas (Index Level)", "df_comp_mas (Component Level 0)"],
        tablefmt="grid"
    ))

    print(f"\n{'=' * 30}\nTEST COMPLETED\n{'=' * 30}")