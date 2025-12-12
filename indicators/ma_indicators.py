# ma_indicators.py
"""
Modular MA / VWMA calculation and plotting utilities (Approach 1).
This module expects callers to supply dataframes (loaded elsewhere),
and an application Config dataclass.

Primary functions:
 - prepare_plot_data(index_df, eod_df, config) -> PlotSetup
 - calculate_idx_and_mkt_ma_vwma(index_df, eod_df) -> (df_idx_with_mas, df_eod_with_mas)
 - calculate_ma_vwma_max_min(df_idx_with_mas, setup, ...) -> df_idx_with_osc
 - calculate_tickers_over_under_mas(df_idx_with_mas, df_eod_with_mas, setup_or_num_tickers) -> df_idx_aggregates
 - calculate_compressao_dispaersao(df_idx_with_mas, df_eod_with_mas, setup) -> (df_idx_compression, df_eod_compression)
 - plot_index_vs_ma_vwma(df_to_plot, setup) -> matplotlib.Figure
 - plot_tickers_over_under_mas(df_to_plot, setup) -> matplotlib.Figure
 - plot_compression_dispersion(df_to_plot, setup) -> matplotlib.Figure
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Project constants (assumed present in your project)
import core.constants
from core.my_data_types import Config, PlotSetup


# ---------------------------
# Calculations
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


def calculate_ma_vwma_max_min(df_idx_with_mas_vwmas: pd.DataFrame,
                              plot_setup: PlotSetup,
                              oscillator_lookback: int = 252,
                              oscillator_type: str = 'minmax')\
        -> pd.DataFrame:
    """
    Compute MA/VWMA ranges, normalize by price, and produce an oscillator scaled for plotting.

    Returns the augmented df_idx dataframe (index-level).
    """
    df_result = df_idx_with_mas_vwmas.copy()

    ma_cols = [c for c in df_result.columns if isinstance(c, str) and c.startswith('MA') and not c.startswith(('MA_', 'VWMA_'))]
    vwma_cols = [c for c in df_result.columns if isinstance(c, str) and c.startswith('VWMA') and not c.startswith(('MA_', 'VWMA_'))]

    ma_cols_no200 = [c for c in ma_cols if not c.endswith('200')]
    vwma_cols_no200 = [c for c in vwma_cols if not c.endswith('200')]

    if ma_cols:
        df_result['MA_max'] = df_result[ma_cols].max(axis=1)
        df_result['MA_min'] = df_result[ma_cols].min(axis=1)
        df_result['MA_range'] = df_result['MA_max'] - df_result['MA_min']
    if ma_cols_no200:
        df_result['MA_no200_max'] = df_result[ma_cols_no200].max(axis=1)
        df_result['MA_no200_min'] = df_result[ma_cols_no200].min(axis=1)
        df_result['MA_no200_range'] = df_result['MA_no200_max'] - df_result['MA_no200_min']

    if vwma_cols:
        df_result['VWMA_max'] = df_result[vwma_cols].max(axis=1)
        df_result['VWMA_min'] = df_result[vwma_cols].min(axis=1)
        df_result['VWMA_range'] = df_result['VWMA_max'] - df_result['VWMA_min']
    if vwma_cols_no200:
        df_result['VWMA_no200_max'] = df_result[vwma_cols_no200].max(axis=1)
        df_result['VWMA_no200_min'] = df_result[vwma_cols_no200].min(axis=1)
        df_result['VWMA_no200_range'] = df_result['VWMA_no200_max'] - df_result['VWMA_no200_min']

    # normalize by price
    eps = 1e-9
    if 'Adj Close' not in df_result.columns:
        raise KeyError("df_idx_with_mas_vwmas must contain 'Adj Close' for normalization")
    price = df_result['Adj Close']

    df_result['MA_no200_range_pct'] = df_result['MA_no200_range'] / (price + eps)
    df_result['VWMA_no200_range_pct'] = df_result['VWMA_no200_range'] / (price + eps)

    # create oscillator unsing minmax or zscore
    if oscillator_type == 'minmax':
        roll_min_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).min()
        roll_max_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).max()
        denom_ma = (roll_max_ma - roll_min_ma).replace(0, np.nan)
        df_result['MA_no200_osc'] = ((df_result['MA_no200_range_pct'] - roll_min_ma) / denom_ma).clip(0.0, 1.0).fillna(0.0)

        roll_min_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).min()
        roll_max_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).max()
        denom_v = (roll_max_v - roll_min_v).replace(0, np.nan)
        df_result['VWMA_no200_osc'] = ((df_result['VWMA_no200_range_pct'] - roll_min_v) / denom_v).clip(0.0, 1.0).fillna(0.0)

    elif oscillator_type == 'zscore':
        roll_mean_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).mean()
        roll_std_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).std().replace(0, np.nan)
        df_result['MA_no200_osc'] = ((df_result['MA_no200_range_pct'] - roll_mean_ma) / roll_std_ma).fillna(0.0)

        roll_mean_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).mean()
        roll_std_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).std().replace(0, np.nan)
        df_result['VWMA_no200_osc'] = ((df_result['VWMA_no200_range_pct'] - roll_mean_v) / roll_std_v).fillna(0.0)

    else:
        raise ValueError("oscillator must be 'minmax' or 'zscore'")

    # scale oscillator for plotting (20% of plot height)
    scale = 0.2 * (plot_setup.ymax - plot_setup.ymin) if (plot_setup.ymax - plot_setup.ymin) != 0 else 1.0
    offset = plot_setup.ymin
    df_result['VWMA_no200_osc_scaled'] = df_result['VWMA_no200_osc'] * scale + offset

    df_ma_vwma_osc = df_result.copy()

    return df_ma_vwma_osc


def calculate_tickers_over_under_mas(df_idx_with_mas_vwmas: pd.DataFrame,
                                     df_eod_with_mas_vwmas: pd.DataFrame,
                                     plot_setup : PlotSetup)\
        -> pd.DataFrame:
    """
    Count how many tickers are above/below each MA/VWMA and return a DataFrame of aggregated index-level stats.

    Parameters
    ----------

    plot_setup : either PlotSetup (uses .num_tickers) or int specifying number of tickers.
    """
    num_tickers = plot_setup.num_tickers

    close_eod = df_eod_with_mas_vwmas['Adj Close']
    compare_frames = []  # List

    for ma in core.constants.mas_list:
        sma_df = df_eod_with_mas_vwmas[f"MA{ma}"]  # series
        vwma_df = df_eod_with_mas_vwmas[f"VWMA{ma}"]  # series

        # Create dataframe of -1, 0 or 1 if under/==/over MA
        ma_comp_df = (close_eod > sma_df).astype(int) - (close_eod < sma_df).astype(int)  #series
        vwma_comp_df = (close_eod > vwma_df).astype(int) - (close_eod < vwma_df).astype(int)  # series

        compare_frames.append((f"Num>MA{ma}-num<MA{ma}", ma_comp_df))
        compare_frames.append((f"Num>VWMA{ma}-num<VWMA{ma}", vwma_comp_df))

    df_eod_above_below_mas = pd.concat([frame for _, frame in compare_frames], axis=1, keys=[label for label, _ in compare_frames])

    number_tickers_above_mas = (df_eod_above_below_mas == 1).T.groupby(level=0).sum().T
    number_tickers_below_mas = (df_eod_above_below_mas == -1).T.groupby(level=0).sum().T
    number_tickers_above_below_sum = df_eod_above_below_mas.T.groupby(level=0).sum().T

    percent_tickers_above_mas = (number_tickers_above_mas / num_tickers) * 100
    percent_tickers_below_mas = (number_tickers_below_mas / num_tickers) * 100
    percent_tickers_above_below_sum = (number_tickers_above_below_sum / num_tickers) * 100

    combined_frames = []
    for ma in core.constants.mas_list:
        for label_type in ["MA", "VWMA"]:
            label = f"{label_type}{ma}"
            df_count_label = f"Num>{label}-num<{label}"

            combined = pd.DataFrame(index=df_idx_with_mas_vwmas.index)
            combined[label] = df_idx_with_mas_vwmas[label]

            combined[f"Nº>{label}"] = number_tickers_above_mas[df_count_label]
            combined[f"Nº<{label}"] = number_tickers_below_mas[df_count_label]
            combined[f"%>{label}"] = percent_tickers_above_mas[df_count_label]
            combined[f"%<{label}"] = percent_tickers_below_mas[df_count_label]
            combined[f"%±{label}"] = percent_tickers_above_below_sum[df_count_label]

            combined_frames.append(combined)

    df_idx_num_percent_above_below_mas_vwmas = pd.concat(combined_frames, axis=1)

    return df_idx_num_percent_above_below_mas_vwmas


def calculate_compressao_dispersao(df_idx_with_mas_vwmas: pd.DataFrame,
                                    df_eod_with_mas_vwmas: pd.DataFrame
                                    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
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


