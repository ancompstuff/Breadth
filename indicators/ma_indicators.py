# =============================================================================
# Imports & Globals
# =============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import get_file
import json
import get_dictionary as gd
from dataclasses import dataclass
import core.constants

# --- DEBUG TOGGLE START ---
DEBUG = False  # Set to True to enable debug output


def debug(msg, df=None):
    """
    Prints a message and optionally the head of a pandas DataFrame
    only if the global DEBUG flag is True.
    """
    if DEBUG:
        print(f"[DEBUG] {msg}")
        if df is not None:
            # Check if the dataframe is a MultiIndex to format output nicely
            if isinstance(df.columns, pd.MultiIndex):
                print("--- MultiIndex DataFrame Columns and Head ---")
                print(df_eod_with_mas_vwmas.columns.get_level_values(0).unique().tolist())
                print(df.head())
            else:
                print("--- DataFrame Columns and Head ---")
                print(df.columns)
                print(df.head())
            print("--------------------------")


# --- DEBUG TOGGLE END ---

# =============================================================================

# =============================================================================
# Dataclass to reduce repetitive plotting code
@dataclass
class PlotSetup:
    """Container for all common plotting parameters."""
    idx: str
    mkt: str
    df_to_plot: pd.DataFrame
    lookback_period: int
    num_tickers: int
    sample_start: str
    sample_end: str
    ymin: float
    ymax: float
    date_labels: list[str]
    tick_positions: list[int]
    xlabel_separation: int

    def apply_xaxis(self, ax: plt.Axes):
        """
        Apply common x-axis formatting (ticks, labels, rotation)
        to the provided Matplotlib axis.
        """
        # 'Date' is a column, tick_positions are integer offsets
        ax.set_xticks(self.tick_positions)
        ax.set_xticklabels(
            [self.date_labels[i] for i in self.tick_positions],
            rotation=45,
            fontsize=8
        )


# =============================================================================

#######################################################################################################
def prepare_plot_data(df_idx: pd.DataFrame, df_eod, dictionary: dict) -> PlotSetup:
    #######################################################################################################
    lookback_period = dictionary["graph_lookback"]
    number_xlabels = 50
    xlabel_separation = max(1, int(lookback_period / number_xlabels))
    idx = next(iter(dictionary["market_to_study"].values()))["idx_code"]
    mkt = next(iter(dictionary["market_to_study"].values()))["market"]

    # Count number of tickers
    if isinstance(df_eod.columns, pd.MultiIndex):
        num_tickers = df_eod.columns.get_level_values(1).nunique()
    else:
        num_tickers = len(df_eod.columns)

    plot_data = df_idx.tail(lookback_period).copy()
    sample_start = plot_data.index.min().strftime('%d/%m/%y')
    sample_end = plot_data.index.max().strftime('%d/%m/%y')
    ymin = plot_data['Adj Close'].min()
    ymax = plot_data['Adj Close'].max()

    plot_data_indexed = plot_data.reset_index()
    date_labels = plot_data_indexed['Date'].dt.strftime("%d/%m/%y").tolist()
    df_to_plot = plot_data_indexed  # .drop(columns=['Date'])

    tick_positions = list(range(0, len(df_to_plot), xlabel_separation))
    last_pos = len(df_to_plot) - 1
    if last_pos not in tick_positions:
        if tick_positions and (last_pos - tick_positions[-1] <= 5):
            tick_positions[-1] = last_pos
        else:
            tick_positions.append(last_pos)

    return PlotSetup(
        idx,
        mkt,
        df_to_plot,
        lookback_period,
        num_tickers,
        sample_start,
        sample_end,
        ymin,
        ymax,
        date_labels,
        tick_positions,
        xlabel_separation
    )


#######################################################################################################
def calculate_idx_and_mkt_ma_vwma(df_idx, df_eod):
    #######################################################################################################
    """
    Calculate moving averages (MAs) and volume-weighted moving averages (VWMAs) for both
    the index and individual tickers.

    Parameters:
    -----------
    df_idx : pd.DataFrame
        DataFrame containing index data with 'Adj Close' and 'Volume' columns
    df_eod : pd.DataFrame
        MultiIndex DataFrame containing ticker data with 'Adj Close' and 'Volume' columns
    dictionary : dict
        Configuration dictionary containing market study parameters

    Returns:
    --------
    tuple:
        df_idx_with_mas_vwmas : pd.DataFrame
            Index data with MA and VWMA columns added:
            Index(['Adj Close', 'Volume', 'MA5', 'VWMA5', 'MA12', 'VWMA12', 'MA25',
            'VWMA25', 'MA40', 'VWMA40', 'MA50', 'VWMA50', 'MA80', 'VWMA80', 'MA100',
            'VWMA100', 'MA200', 'VWMA200'],
            dtype='object')

        df_eod_with_mas_vwmas : pd.DataFrame
            Ticker (level 1) data with MA and VWMA columns (level 0)added:
            ['Adj Close', 'Volume', 'MA5', 'VWMA5', 'MA12', 'VWMA12', 'MA25', 'VWMA25',
             'MA40', 'VWMA40', 'MA50', 'VWMA50', 'MA80',
             'VWMA80', 'MA100', 'VWMA100', 'MA200', 'VWMA200']
    """
    # ====================================
    # Calculate INDEX MAs and VWMAs
    # ====================================
    close = df_idx['Adj Close']
    volume = df_idx['Volume']

    results = {}
    for ma in core.constants.mas_list:
        sma = close.rolling(window=ma).mean()
        vwma = (close * volume).rolling(window=ma).sum() / volume.rolling(window=ma).sum()
        results[f"MA{ma}"] = sma
        results[f"VWMA{ma}"] = vwma

    # ---------------------------------------------------------------------------------
    # df_idx with MAs and VWMAs
    df_idx_with_mas_vwmas = pd.concat([df_idx, pd.DataFrame(results)], axis=1)
    # ---------------------------------------------------------------------------------

    # ===================================
    # Calculate MKT TICKER MAs and VWMAs
    # ===================================
    close_eod = df_eod['Adj Close']
    vol_eod = df_eod['Volume']

    eod_frames = []
    for ma in core.constants.mas_list:
        sma_df = close_eod.rolling(window=ma).mean()
        vwma_df = (close_eod * vol_eod).rolling(window=ma).sum() / vol_eod.rolling(window=ma).sum()
        eod_frames.append((f"MA{ma}", sma_df))
        eod_frames.append((f"VWMA{ma}", vwma_df))

        """ eod_frames looks like:
            [('MA10', <DataFrame>), ('VWMA10', <DataFrame>),
            ('MA20', <DataFrame>), ('VWMA20', <DataFrame>), ...
                       ]"""
    # Stack the frames horizontally and add the keys as a new top-level column index.
    df_eod_with_mas_vwmas = pd.concat(
        [frame for _, frame in eod_frames],
        axis=1,
        keys=[label for label, _ in eod_frames]
    )
    # Add Adj Close and Volume for each ticker
    df_eod_with_mas_vwmas = pd.concat(
        [df_eod[['Adj Close', 'Volume']],  # add original data
         df_eod_with_mas_vwmas],
        axis=1
    )

    # Get the column headers for the first DataFrame
    headers_idx = df_idx_with_mas_vwmas.columns
    # Get the column headers for the second DataFrame
    headers_eod = df_eod_with_mas_vwmas.columns.get_level_values(0).unique().tolist()
    print("--- Headers for df_idx_with_mas_vwmas ---")
    print(headers_idx)
    print("\n--- Level 0 headers for df_eod_with_mas_vwmas ---")
    print(headers_eod)

    # ---------------------------------------------------------------------------------
    return (df_idx_with_mas_vwmas, df_eod_with_mas_vwmas)
    # ---------------------------------------------------------------------------------


def calculate_ma_vwma_max_min(df_idx_with_mas_vwmas, setup, oscillator_lookback=252,
                              oscillator='minmax', ):  # or zscore
    # Make a copy of the input DataFrame to avoid modifying the original
    df_result = df_idx_with_mas_vwmas.copy()

    # Identify MA and VWMA columns (excluding any that might already be in the result)
    ma_cols = [
        col for col in df_result.columns
        if col.startswith('MA')
           and not col.startswith(('MA_', 'VWMA_'))
    ]
    vwma_cols = [
        col for col in df_result.columns
        if col.startswith('VWMA')
           and not col.startswith(('MA_', 'VWMA_'))
    ]
    # Now filter out the 200 MA/VWMA too
    ma_cols_no200 = [c for c in ma_cols if not c.endswith('200')]
    vwma_cols_no200 = [c for c in vwma_cols if not c.endswith('200')]

    # Compute max, min, and range for MAs
    if ma_cols:  # All MAs
        ma_values = df_result[ma_cols]
        df_result['MA_max'] = ma_values.max(axis=1)
        df_result['MA_min'] = ma_values.min(axis=1)
        df_result['MA_range'] = df_result['MA_max'] - df_result['MA_min']
    if ma_cols_no200:
        ma_no200_values = df_result[ma_cols_no200]
        df_result['MA_no200_max'] = ma_no200_values.max(axis=1)
        df_result['MA_no200_min'] = ma_no200_values.min(axis=1)
        df_result['MA_no200_range'] = df_result['MA_no200_max'] - df_result['MA_no200_min']

    # Compute max, min, and range for VWMAs
    if vwma_cols:  # All VWMAs
        vwma_values = df_result[vwma_cols]
        df_result['VWMA_max'] = vwma_values.max(axis=1)
        df_result['VWMA_min'] = vwma_values.min(axis=1)
        df_result['VWMA_range'] = df_result['VWMA_max'] - df_result['VWMA_min']
    if vwma_cols_no200:  # No VA200
        vwma_no200_values = df_result[vwma_cols_no200]
        df_result['VWMA_no200_max'] = vwma_no200_values.max(axis=1)
        df_result['VWMA_no200_min'] = vwma_no200_values.min(axis=1)
        df_result['VWMA_no200_range'] = df_result['VWMA_no200_max'] - df_result['VWMA_no200_min']

    # ---------------------------------------------------------
    # --- Normalize by price to remove raw price dependence ---
    # ---------------------------------------------------------
    eps = 1e-9  # prefer dividing by a smooth price (Adj Close is fine); small epsilon to avoid 0-div
    price = df_result.get('Adj Close', None)
    if price is None:
        raise KeyError("df must contain 'Adj Close' column for normalization")

    df_result['MA_no200_range_pct'] = df_result['MA_no200_range'] / (price + eps)
    df_result['VWMA_no200_range_pct'] = df_result['VWMA_no200_range'] / (price + eps)

    # --- Create oscillators ---
    if oscillator == 'minmax':
        # rolling min/max -> scale into 0..1 over `oscillator_lookback` history (causal)
        roll_min_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).min()
        roll_max_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).max()
        denom_ma = (roll_max_ma - roll_min_ma).replace(0, np.nan)
        df_result['MA_no200_osc'] = (df_result['MA_no200_range_pct'] - roll_min_ma) / denom_ma
        df_result['MA_no200_osc'] = df_result['MA_no200_osc'].clip(0.0, 1.0).fillna(0.0)

        roll_min_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).min()
        roll_max_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).max()
        denom_v = (roll_max_v - roll_min_v).replace(0, np.nan)
        df_result['VWMA_no200_osc'] = (df_result['VWMA_no200_range_pct'] - roll_min_v) / denom_v
        df_result['VWMA_no200_osc'] = df_result['VWMA_no200_osc'].clip(0.0, 1.0).fillna(0.0)

    elif oscillator == 'zscore':
        # rolling mean/std -> standardized oscillator centered at 0
        roll_mean_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).mean()
        roll_std_ma = df_result['MA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).std().replace(
            0, np.nan)
        df_result['MA_no200_osc'] = (df_result['MA_no200_range_pct'] - roll_mean_ma) / roll_std_ma
        df_result['MA_no200_osc'] = df_result['MA_no200_osc'].fillna(0.0)

        roll_mean_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).mean()
        roll_std_v = df_result['VWMA_no200_range_pct'].rolling(window=oscillator_lookback, min_periods=1).std().replace(
            0, np.nan)
        df_result['VWMA_no200_osc'] = (df_result['VWMA_no200_range_pct'] - roll_mean_v) / roll_std_v
        df_result['VWMA_no200_osc'] = df_result['VWMA_no200_osc'].fillna(0.0)

    else:
        raise ValueError("oscillator must be 'minmax' or 'zscore'")

    # Optional: smooth the oscillator (e.g., short EMA) if desired for plotting

    # df_result['VWMA_no200_osc_smooth'] = df_result['VWMA_no200_osc'].ewm(span=5, adjust=False).mean()

    # -----------------------------------------------------------
    # Scale the oscillator for better visualization when plotting
    # -----------------------------------------------------------
    scale = 0.2 * (setup.ymax - setup.ymin)  # oscillator will be 20% of plot height
    offset = setup.ymin
    df_result['VWMA_no200_osc_scaled'] = df_result['VWMA_no200_osc'] * scale + offset

    df_idx_with_mas_vwmas_max_min_oscil = df_result

    # Get the column headers for the first DataFrame
    headers_idx = df_idx_with_mas_vwmas_max_min_oscil.columns
    print("--- Headers for df_idx_with_mas_vwmas ---")
    print(headers_idx)

    return df_idx_with_mas_vwmas_max_min_oscil


# ----------------------------------------------------------------------------------
def calculate_tickers_over_under_mas(df_idx_with_mas_vwmas, df_eod_with_mas_vwmas, dictionary):
    """ Headers for df_idx_with_mas_vwmas_and_above_below_calculations:
        Index(
        ['MA5','Nº>MA5','Nº<MA5','%>MA5','%<MA5','%±MA5','VWMA5','Nº>VWMA5','Nº<VWMA5','%>VWMA5','%<VWMA5','%±VWMA5',
        'MA12','Nº>MA12','Nº<MA12','%>MA12','%<MA12','%±MA12','VWMA12','Nº>VWMA12','Nº<VWMA12','%>VWMA12','%<VWMA12','%±VWMA12',
         'MA25','Nº>MA25','Nº<MA25','%>MA25','%<MA25','%±MA25','VWMA25','Nº>VWMA25','Nº<VWMA25','%>VWMA25','%<VWMA25','%±VWMA25',
         'MA40','Nº>MA40','Nº<MA40','%>MA40','%<MA40','%±MA40','VWMA40','Nº>VWMA40','Nº<VWMA40','%>VWMA40','%<VWMA40','%±VWMA40',
         'MA50','Nº>MA50','Nº<MA50','%>MA50','%<MA50','%±MA50','VWMA50','Nº>VWMA50','Nº<VWMA50','%>VWMA50','%<VWMA50','%±VWMA50',
         'MA80','Nº>MA80','Nº<MA80','%>MA80','%<MA80','%±MA80','VWMA80','Nº>VWMA80','Nº<VWMA80','%>VWMA80','%<VWMA80','%±VWMA80',
         'MA100','Nº>MA100','Nº<MA100','%>MA100','%<MA100','%±MA100',
         'VWMA100','Nº>VWMA100','Nº<VWMA100','%>VWMA100','%<VWMA100','%±VWMA100',
         'MA200','Nº>MA200','Nº<MA200','%>MA200','%<MA200','%±MA200',
         'VWMA200','Nº>VWMA200','Nº<VWMA200','%>VWMA200','%<VWMA200','%±VWMA200'],
      dtype='object')"""
    # ----------------------------------------------------------------------------------
    close_eod = df_eod_with_mas_vwmas['Adj Close']
    num_tickers = dictionary["number_tickers"]
    compare_frames = []

    for ma in core.constants.mas_list:
        sma_df = df_eod_with_mas_vwmas[("MA" + str(ma))]
        vwma_df = df_eod_with_mas_vwmas[("VWMA" + str(ma))]

        # Calculate if ticker close is above (1), below (-1) or same (0) as MA/VWMA
        ma_comp_df = (close_eod > sma_df).astype(int) - (close_eod < sma_df).astype(int)
        vwma_comp_df = (close_eod > vwma_df).astype(int) - (close_eod < vwma_df).astype(int)

        # Add comparison frames (above/below)
        compare_frames.append((f"$<>MA{ma}", ma_comp_df))
        compare_frames.append((f"$<>VWMA{ma}", vwma_comp_df))

    df_eod_above_below_mas = pd.concat(
        [frame for _, frame in compare_frames],
        axis=1,
        keys=[label for label, _ in compare_frames]
    )

    # Get the column headers for the DataFrame
    headers_eod = df_eod_above_below_mas.columns.get_level_values(0).unique().tolist()
    print("\n--- Headers df_eod_above_below_mas ---")
    print(headers_eod)

    # ---------------------------------------------------
    # Count tickers above/below each MA
    # ---------------------------------------------------
    number_tickers_above_mas = (df_eod_above_below_mas == 1).T.groupby(level=0).sum().T
    number_tickers_below_mas = (df_eod_above_below_mas == -1).T.groupby(level=0).sum().T
    number_tickers_above_below_sum = df_eod_above_below_mas.T.groupby(level=0).sum().T

    # ---------------------------------------------------
    # Convert counts to percentages
    # ---------------------------------------------------
    percent_tickers_above_mas = (number_tickers_above_mas / num_tickers) * 100
    percent_tickers_below_mas = (number_tickers_below_mas / num_tickers) * 100
    percent_tickers_above_below_sum = (number_tickers_above_below_sum / num_tickers) * 100

    # ---------------------------------------------------
    # Combine all data into one DataFrame
    # ---------------------------------------------------
    combined_frames = []

    for ma in core.constants.mas_list:
        for label_type in ["MA", "VWMA"]:
            label = f"{label_type}{ma}"
            df_count_label = f"$<>{label}"

            combined = pd.DataFrame(index=df_idx_with_mas_vwmas.index)
            combined[label] = df_idx_with_mas_vwmas[label]

            combined[f"Nº>{label}"] = number_tickers_above_mas[df_count_label]
            combined[f"Nº<{label}"] = number_tickers_below_mas[df_count_label]
            combined[f"%>{label}"] = percent_tickers_above_mas[df_count_label]
            combined[f"%<{label}"] = percent_tickers_below_mas[df_count_label]
            combined[f"%±{label}"] = percent_tickers_above_below_sum[df_count_label]

            combined_frames.append(combined)

    df_idx_num_percent_above_below_mas_vwmas = pd.concat(combined_frames, axis=1)

    # Get the column headers for DataFrame
    headers_idx = df_idx_num_percent_above_below_mas_vwmas.columns
    print("--- Headers for df_idx_num_percent_above_below_mas_vwmas ---")
    print(headers_idx)

    return df_idx_num_percent_above_below_mas_vwmas


# ----------------------------------------------------------------------------------
def plot_index_vs_ma_vwma(df_to_plot, setup):
    # ----------------------------------------------------------------------------------
    plot = 'Plot 1'
    df_to_plot = df_to_plot.tail(setup.lookback_period)
    # --- Create figure and subplots ---
    fig, axs = plt.subplots(2, 1, figsize=(18, 9), sharex=True)

    # ------------------
    # TOP SUBPLOT - SMAs
    # ------------------
    ax = axs[0]
    ax2 = ax.twinx()  # right axis for volume

    ax.set_title(
        f"{plot}: {setup.idx} ({setup.num_tickers} tickers) preço vs Médias Móveis. "
        f"{setup.sample_start}-{setup.sample_end}",
        fontsize=12, fontweight="bold"
    )

    # Left axis: fill and plot price
    ax.fill_between(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='lightgrey')
    ax.plot(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='black')  # , label='Preço')
    ax.set_ylim(setup.ymin, setup.ymax)
    ax.set_ylabel('Preço e Médias Móveis', fontsize=9)

    # Plot SMAs
    for ma in core.constants.mas_list:
        col = f"MA{ma}"
        ax.plot(setup.df_to_plot.index, df_to_plot[col], color=core.constants.ma_color_map[col], label=col, zorder=5)

    # Plot MA range (no 200)
    ax.bar(setup.df_to_plot.index,
           df_to_plot['MA_no200_range'],
           bottom=setup.ymin,  # anchor the bars at the bottom of your visible range
           color='yellow',
           width=0.8,
           label='MA range (no 200)',
           alpha=0.6,
           zorder=3
           )
    # Plot MA range
    ax.bar(setup.df_to_plot.index,
           df_to_plot['MA_range'],
           bottom=setup.ymin,  # anchor the bars at the bottom of your visible range
           color='orange',
           width=0.9,
           label='MA range',
           alpha=0.8,
           zorder=2
           )

    ax.tick_params(axis='y', labelsize=8)
    ax.grid(True, axis='both')

    # Right axis: volume
    ax2.bar(setup.df_to_plot.index, setup.df_to_plot['Volume'], width=1.0, color='blue', alpha=0.3, zorder=1,
            label='Volume')
    ax2.set_ylabel('Volume', fontsize=9)
    ax2.tick_params(axis='y', labelsize=9)

    # Combine legends from all axes
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2,
               labels + labels2,
               loc='upper left',
               fontsize=8,
               frameon=True
               )
    # ---------------------
    # LOWER SUBPLOT - VWMAs
    # ---------------------
    ax = axs[1]
    ax2 = ax.twinx()
    ax.grid(True, axis='both')

    ax.set_title(
        f"{setup.idx} preço vs Médias Móveis ponderadas por Volume",
        fontsize=12, fontweight="bold"
    )

    # Left axis: fill and plot price
    ax.fill_between(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='lightgrey')
    ax.plot(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='black')  # , label='Preço')
    ax.set_ylim(setup.ymin, setup.ymax)
    ax.set_ylabel('Preço e M.Móv p.p. Volume', fontsize=9)

    # Plot VWMAs
    for ma in core.constants.mas_list:
        col = f"VWMA{ma}"
        ax.plot(setup.df_to_plot.index,
                df_to_plot[col],
                color=core.constants.ma_color_map[col],
                label=col,
                zorder=5)

    # Plot VWMA range (no 200)
    ax.bar(setup.df_to_plot.index, df_to_plot['VWMA_no200_range'],
           bottom=setup.ymin,  # anchor the bars at the bottom of your visible range
           color='yellow',
           width=0.9,
           label='VWMA range (no 200)',
           alpha=0.6,
           zorder=3
           )
    # Plot VWMA range
    ax.bar(setup.df_to_plot.index, df_to_plot['VWMA_range'],
           bottom=setup.ymin,  # anchor the bars at the bottom of your visible range
           color='orange',
           width=0.9,
           label='VWMA range',
           alpha=0.8,
           zorder=2
           )
    # Plot VWMA oscillator
    ax.bar(setup.
           df_to_plot.index, df_to_plot['VWMA_no200_osc_scaled'],
           # bottom=(setup.ymax + setup.ymin)/2,  # anchor the bars at the bottom of your visible range
           color='green',
           width=1.0,
           label='VWMA range oscillator (0-1)',
           alpha=0.9,
           zorder=2
           )
    scale = 0.2 * (setup.ymax - setup.ymin) + setup.ymin
    ax.axhline(y=scale, color='green', linestyle='--', linewidth=2.0, alpha=0.9)

    ax.tick_params(axis='y', labelsize=8)
    ax.grid(True, axis='both')

    # Right axis: volume
    ax2.bar(setup.df_to_plot.index, setup.df_to_plot['Volume'], width=1.0, color='blue', alpha=0.3, zorder=1,
            label='Volume')
    ax2.set_ylabel('Volume', fontsize=9)
    ax2.tick_params(axis='y', labelsize=9)

    # X-axis formatting using PlotSetup (only on bottom subplot for shared x-axis)
    setup.apply_xaxis(ax)

    # Combine legends from all axes
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2,
               labels + labels2,
               loc='upper left',
               fontsize=8,
               frameon=True
               )

    return fig


# ----------------------------------------------------------------------------------
def plot_tickers_over_under_mas(df_to_plot, setup):  # uses df_idx_with_mas_vwmas_and_above_below_calculations
    # ----------------------------------------------------------------------------------
    df_to_plot = df_to_plot.tail(setup.lookback_period)
    plot = 'Plot 2'
    plot_configs = [
        ('Plot 2.1', "Papeís acima VWMAs curtas menos papeís abaixo (%)", ["%±MA5", "%±MA12", "%±MA25"],
         ["%±VWMA5", "%±VWMA12", "%±VWMA25"], "short"),
        ('Plot 2.2', "Papeís acima VWMAs curtas médias (Worden/Eden) menos papeís abaixo (%)", ["%±MA40", "%±MA80"],
         ["%±VWMA40", "%±VWMA80"], "mid"),
        ('Plot 2.3', "Papeís acima VWMAs longas menos papeís abaixo (%)", ["%±MA50", "%±MA100", "%±MA200"],
         ["%±VWMA50", "%±VWMA100", "%±VWMA200"], "long")
    ]
    # --- Prepare PlotSetup ---
    num_tickers = setup.num_tickers
    # --- Create figure and subplots ---
    fig, axs = plt.subplots(3, 1, figsize=(18, 9), sharex=True)

    for pc in range(len(plot_configs)):
        ax = axs[pc]
        ax_twin = ax.twinx()  # right axis for volume

        title_dates = ""
        # Only add the date range if it is the first subplot (pc == 0)
        if pc == 0:
            title_dates = f": {setup.sample_start}-{setup.sample_end}"
        ax.set_title(
            f"{setup.mkt}: {plot_configs[pc][1]}"
            f"{title_dates}",
            fontsize=12, fontweight="bold"
        )
        # Left axis: fill and plot price
        ax.fill_between(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='lightgrey')
        ax.plot(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='black')  # , label='Preço')
        ax.set_ylim(setup.ymin, setup.ymax)
        ax.set_ylabel('Preço', fontsize=9)

        # Right axis: VWMAs
        group_key = plot_configs[pc][4]  # e.g., "short", "mid", "long"
        for ma in core.constants.ma_groups[group_key]["periods"]:  # Accesses ma_groups["short"]["periods"]
            col = f"%±VWMA{ma}"
            ax_twin.plot(setup.df_to_plot.index, df_to_plot[col], color=core.constants.ma_color_map[col], label=col)
            ax_twin.axhline(y=0, color='black', linestyle='--')
            # Add the conditional filling
            # Fill green where the curve is >= 0
            ax_twin.fill_between(
                setup.df_to_plot.index,
                df_to_plot[col],
                0,
                where=(df_to_plot[col] >= 0),
                color='green',
                alpha=0.5,
                interpolate=True
            )
            # Fill red where the curve is <= 0
            ax_twin.fill_between(
                setup.df_to_plot.index,
                df_to_plot[col],
                0,
                where=(df_to_plot[col] <= 0),
                color='red',
                alpha=0.5,
                interpolate=True
            )
        ax_twin.set_ylabel(f'% papéis ({setup.num_tickers} papéis)', fontsize=9)
        ax_twin.legend(loc='upper left')

        ax.grid(True, axis='x')
        ax_twin.grid(True, axis='y')

        # X-axis formatting using PlotSetup (only on bottom subplot for shared x-axis)
        setup.apply_xaxis(ax)

        # Combine legends from all axes
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax_twin.get_legend_handles_labels()
        ax_twin.legend(lines + lines2,
                       labels + labels2,
                       loc='upper left',
                       fontsize=8,
                       frameon=True
                       )
    return fig


# --------------------------------------------------------------------------------------------------
def calculate_compressao_dispaersao(df_idx_with_mas_vwmas: pd.DataFrame, df_eod_with_mas_vwmas, dict):
    # --------------------------------------------------------------------------------------------------
    df_idx_compression = df_idx_with_mas_vwmas.copy()
    df_eod_compression = df_eod_with_mas_vwmas.copy()

    close_eod = df_eod_compression['Adj Close']

    for ma in core.constants.mas_list:
        # Compute difference DataFrames with ticker columns
        diff_ma_col = f"C-MA{ma}"
        diff_vwma_col = f"C-VWMA{ma}"

        # Compute difference DataFrames with ticker columns
        diff_ma_df = (close_eod - df_eod_compression[f"MA{ma}"]) / close_eod
        diff_vwma_df = (close_eod - df_eod_compression[f"VWMA{ma}"]) / close_eod

        # Absolute compression: sum of absolute values across tickers (level 1 columns)
        abs_comp_ma = diff_ma_df.abs().sum(axis=1)
        abs_comp_vwma = diff_vwma_df.abs().sum(axis=1)

        # Directional compression: sum of signed values across tickers
        dir_comp_ma = diff_ma_df.sum(axis=1)
        dir_comp_vwma = diff_vwma_df.sum(axis=1)

        # Create new MultiIndex for these diff columns with new first-level label + ticker second level
        diff_ma_df.columns = pd.MultiIndex.from_product([[diff_ma_col], diff_ma_df.columns])
        diff_vwma_df.columns = pd.MultiIndex.from_product([[diff_vwma_col], diff_vwma_df.columns])

        # Concatenate along columns to df_eod
        df_eod_compression = pd.concat([df_eod_compression, diff_ma_df, diff_vwma_df], axis=1)

        # -------------------------------------------------------------------------
        # ADICIONANDO AS SÉRIES DE COMPRESSÃO AO DF_IDX
        # df_idx é um DataFrame simples, então a atribuição direta é o metodo correto
        # -------------------------------------------------------------------------
        df_idx_compression[f"Abs_C-MA{ma}"] = abs_comp_ma
        df_idx_compression[f"Abs_C-VWMA{ma}"] = abs_comp_vwma
        df_idx_compression[f"Dir_C-MA{ma}"] = dir_comp_ma
        df_idx_compression[f"Dir_C-VWMA{ma}"] = dir_comp_vwma
        # -------------------------------------------------------------------------

    # ---------------------------------------------------------
    # AGGREGATE ABS_C-VWMA BY GROUP (short, mid, long)
    # ---------------------------------------------------------
    for group_name, ma_list in core.constants.ma_groups.items():
        # Access the list of periods using the "periods" key
        periods_list = ma_list["periods"]

        abs_cols_to_sum = [f"Abs_C-VWMA{ma}" for ma in periods_list]
        dir_cols_to_sum = [f"Dir_C-VWMA{ma}" for ma in periods_list]

        # Filter to existing columns only (avoids KeyErrors if some MA missing)
        abs_cols_to_sum = [c for c in abs_cols_to_sum if c in df_idx_compression.columns]
        dir_cols_to_sum = [d for d in dir_cols_to_sum if d in df_idx_compression.columns]

        df_idx_compression[f"Abs_VWMA_{group_name}_sum"] = df_idx_compression[abs_cols_to_sum].sum(axis=1)
        df_idx_compression[f"Dir_VWMA_{group_name}_sum"] = df_idx_compression[dir_cols_to_sum].sum(axis=1)

        # print(df_eod_compression.tail(3))

    # Get the column headers for DataFrame
    headers_idx = df_idx_compression.columns
    print("--- Headers for df_idx_compression ---")
    print(headers_idx)

    return df_idx_compression, df_eod_compression


# ----------------------------------------------------------------------------------
def plot_compression_dispersion(df_to_plot, setup):  # uses df_idx_with_mas_vwmas_and_above_below_calculations
    # ----------------------------------------------------------------------------------
    df_to_plot = df_to_plot.tail(setup.lookback_period)
    plot = 'Plot 3'
    num_tickers = setup.num_tickers
    title_dates = f": {setup.sample_start}-{setup.sample_end}"
    mkt = setup.mkt

    fig, axs = plt.subplots(3, 1, figsize=(18, 9), sharex=True)

    subplots = {
        axs[0]: {
            "group": "short",
            "port": "curtas",
            "title": f"{mkt}: Compresão/dispersão (soma absoluta) das P-MMppVs (CURTAS, MÉDIAS E LONGAS). {title_dates}",
            "color": "red"
        },
        axs[1]: {
            "group": "mid",
            "port": "médias",
            "title": f"Compresão/dispersão (soma momentum/viés direcionais) das P-MMppVs (CURTAS, MÉDIAS E LONGAS)",
            "color": "blue"
        },
        axs[2]: {
            "group": "long",
            "port": "longas",
            "title": f"Compresão (soma absoluta) das diferenças entre MMppVs LONGAS e preço.",
            "color": "green"
        }
    }
    for ax in axs[:2]:
        # Left axis: fill and plot price
        ax.set_title(subplots[ax]["title"], fontsize=12, fontweight="bold")
        ax.fill_between(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='#F5F5F5')  # 'lightgrey')
        ax.plot(setup.df_to_plot.index, setup.df_to_plot['Adj Close'], color='black', linewidth=1.0, label='Preço')
        ax.set_ylim(setup.ymin, setup.ymax)
        ax.set_ylabel('Preço', fontsize=9)
        ax.grid(True, axis='x')
        setup.apply_xaxis(ax)

    # TOP PLOT: Right axis
    axs0_twin = axs[0].twinx()
    axs0_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Abs_VWMA_{subplots[axs[0]]["group"]}_sum"],
                   color=subplots[axs[0]]["color"],
                   label=f"Soma absoluta P-MMppVs: {subplots[axs[0]]["port"]}")
    axs0_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Abs_VWMA_{subplots[axs[1]]["group"]}_sum"],
                   color=subplots[axs[1]]["color"],
                   label=f"Soma absoluta P-MMppVs: {subplots[axs[1]]["port"]}")
    axs0_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Abs_VWMA_{subplots[axs[2]]["group"]}_sum"],
                   color=subplots[axs[2]]["color"],
                   label=f"Soma absoluta P-MMppVs: {subplots[axs[2]]["port"]}")
    axs0_twin.set_ylabel('Compresão: Soma Absoluta', fontsize=9)
    axs0_twin.grid(True, axis='y')

    lines, labels = axs[0].get_legend_handles_labels()
    lines2, labels2 = axs0_twin.get_legend_handles_labels()
    axs0_twin.legend(lines + lines2, labels + labels2,
                     loc='upper left',
                     fontsize=8,
                     frameon=True
                     )
    # MIDDLE PLOT: Right axis
    axs1_twin = axs[1].twinx()
    axs1_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Dir_VWMA_{subplots[axs[0]]["group"]}_sum"],
                   color=subplots[axs[0]]["color"],
                   label=f"Soma direcional P-MMppvs: {subplots[axs[0]]["port"]}")
    axs1_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Dir_VWMA_{subplots[axs[1]]["group"]}_sum"],
                   color=subplots[axs[1]]["color"],
                   label=f"Soma direcional P-MMppvs: {subplots[axs[1]]["port"]}")
    axs1_twin.plot(setup.df_to_plot.index,
                   df_to_plot[f"Dir_VWMA_{subplots[axs[2]]["group"]}_sum"],
                   color=subplots[axs[2]]["color"],
                   label=f"Soma direcional P-MMppvs: {subplots[axs[2]]["port"]}")
    axs1_twin.axhline(y=0, color='black', linestyle='--', linewidth=2.0)
    axs1_twin.set_ylabel('Soma direcional', fontsize=9)
    axs1_twin.grid(True, axis='y')

    lines, labels = axs[1].get_legend_handles_labels()
    lines2, labels2 = axs1_twin.get_legend_handles_labels()
    axs1_twin.legend(lines + lines2, labels + labels2,
                     loc='upper left',
                     fontsize=8,
                     frameon=True
                     )
    # ---------------------------
    # THIRD SUBPLOT - VWMA HEATMAP
    # ---------------------------
    # ---- Filter ABS first ----
    abs_cols = [
        c for c in df_to_plot.columns
        if c.startswith("Abs_C-VWMA") and any(c.endswith(f"VWMA{ma}") for ma in core.constants.mas_list)
    ]
    # Sort numerically by MA
    abs_cols = sorted(abs_cols, key=lambda c: int(c.split("VWMA")[1]))

    # ---- Filter DIR second ----
    dir_cols = [
        c for c in df_to_plot.columns
        if c.startswith("Dir_C-VWMA") and any(c.endswith(f"VWMA{ma}") for ma in core.constants.mas_list)
    ]
    # Sort numerically by MA
    dir_cols = sorted(dir_cols, key=lambda c: int(c.split("VWMA")[1]))

    # ---- Final combined order ----
    vwma_cols = abs_cols + dir_cols

    # Extract heatmap data (as a matrix: rows=VWMAs, columns=time)
    heat_data = df_to_plot[vwma_cols].T

    # Normalize each row to [0,1] for better color contrast
    heat_data_norm = (heat_data - heat_data.min(axis=1).values[:, None]) / \
                     (heat_data.max(axis=1).values[:, None] - heat_data.min(axis=1).values[:, None] + 1e-9)

    # Plot heatmap
    im = axs[2].imshow(
        heat_data_norm,
        aspect='auto',
        cmap='hot',
        interpolation='nearest'
    )

    # Y-axis labels = VWMA periods
    axs[2].set_yticks(range(len(vwma_cols)))
    axs[2].set_yticklabels(df_to_plot[vwma_cols], fontsize=6)

    # Title
    axs[2].set_title("VWMA Compression Heatmap")

    # X-axis: match index length with evenly spaced ticks
    setup.apply_xaxis(axs[2])

    # Colorbar - shrinks width of x-axis if used
    # fig.colorbar(im, ax=axs[2], fraction=0.02, orientation='vertical')

    return fig


##########################################################################
# -----------------------------MAIN PROGRAM-------------------------------
##########################################################################
if __name__ == "__main__":
    # -------------------------------------------
    # FOLDER LOCATIONS
    # -------------------------------------------
    with open("file_locations.json", "r") as f:
        paths = json.load(f)

    downloaded_data_folder = paths["downloaded_data_folder"]
    '''pdf_folder = paths["pdf_folder"]
    codes_to_download_folder = paths["codes_to_download_folder"]
    yahoo_markets_dictionary = paths["yahoo_markets_dictionary"]
    '''
    config = gd.get_dictionary("config.json")
    data_idx, suf_idx = get_file.get_file("idx", downloaded_data_folder, config, ['Date', 'Adj Close', 'Volume'])
    data_eod, suf_eod = get_file.get_file("eod", downloaded_data_folder, config, ['Date', 'Adj Close', 'Volume'])

    left_axis_plot_setup = prepare_plot_data(data_idx, data_eod['Adj Close'], config)
    print(left_axis_plot_setup.num_tickers)

    # Calculate and plot index vs NA/VWMAs
    (df_idx_with_mas_vwmas, df_eod_with_mas_vwmas) = calculate_idx_and_mkt_ma_vwma(data_idx, data_eod)
    df_idx_with_mas_vwmas_max_min_oscil = calculate_ma_vwma_max_min(df_idx_with_mas_vwmas, setup=left_axis_plot_setup)

    fig = plot_index_vs_ma_vwma(df_idx_with_mas_vwmas_max_min_oscil, left_axis_plot_setup)

    # Calculate and plot tickers above/below NA/VWMAs
    df_idx_with_mas_vwmas_and_above_below_calculations = (
        calculate_tickers_over_under_mas(
            df_idx_with_mas_vwmas,
            df_eod_with_mas_vwmas,
            config)
    )

    fig = plot_tickers_over_under_mas(df_idx_with_mas_vwmas_and_above_below_calculations, setup=left_axis_plot_setup)

    df_idx_compression, df_eod_compression = calculate_compressao_dispaersao(df_idx_with_mas_vwmas,
                                                                             df_eod_with_mas_vwmas, config)
    fig = plot_compression_dispersion(df_idx_compression, left_axis_plot_setup)

    plt.show()

    # The End
