"""
Highs and Lows Plotting
=======================
Creates dual-panel visualization:
1. Top panel: Stacked bars of highs/lows counts + index overlay
2. Bottom panel: Stacked bars of net differences + index overlay
"""

import pandas as pd
import matplotlib.pyplot as plt
from core.my_data_types import PlotSetup


def plot_highs_and_lows(ps: PlotSetup, hl_df: pd.DataFrame) -> plt.Figure:
    """
    Plot highs and lows indicator with two subplots.

    Parameters
    ----------
    ps : PlotSetup
        Plot setup containing index price data, dates, and formatting info
    hl_df : pd.DataFrame
        Result from calculate_highs_and_lows() with all indicator columns

    Returns
    -------
    plt.Figure
        Matplotlib figure with two subplots
    """

    # Extract the data we need
    lookback = ps.lookback_period
    idx = ps.idx

    # Slice data based on lookback for plotting
    p = hl_df.iloc[-lookback:]

    # Reset index to integer for plotting
    p_indexed = p.reset_index()
    date_labels = p_indexed['Date'].dt.strftime("%d/%m/%y").tolist()
    p1 = p_indexed.drop(columns=['Date'])

    # Extract only the raw count columns (not differences)
    raw_cols = ['ATH', 'ATL', '12MH', '12ML', '3MH', '3ML', '1MH', '1ML']
    p1_raw = p1[raw_cols]

    # Extract only the difference columns
    diff_cols = ['ATH-ATL', '12MH-12ML', '3MH-3ML', '1MH-1ML']
    p2 = p1[diff_cols]

    # Get price data (already sliced in ps)
    p_idx = ps.price_data['Adj Close'].values

    #########################################################################
    # CREATE FIGURE
    #########################################################################
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 9), sharex=True)

    start_date = p.index[0].strftime('%d/%m/%y')
    end_date = p.index[-1].strftime('%d/%m/%y')

    #########################################################################
    # SUBPLOT 1: Highs and Lows Counts
    #########################################################################

    # Plot price on left axis
    ax1.plot(ps.plot_index, p_idx, color='black', linestyle='-',
             linewidth=2, label=f'{idx}', alpha=0.7)
    ax1.set_ylabel(f'{idx} preço')
    ax1.tick_params(axis='y', labelcolor='black')

    # Create twin axis for bars
    ax1_twin = ax1.twinx()

    # Define colors for each indicator
    plot_stuff = {
        'ATH': ('deepskyblue', 'Nº papeis no máximo histórico'),
        'ATL': ('saddlebrown', 'Nº no mín histórico'),
        '12MH': ('forestgreen', 'Nº no máx/12 meses'),
        '12ML': ('red', 'Nº no min/12 meses'),
        '3MH': ('mediumseagreen', 'Nº no máx/3 meses'),
        '3ML': ('tomato', 'Nº no min/3 meses'),
        '1MH': ('palegreen', 'Nº no máx/1 mes'),
        '1ML': ('peachpuff', 'Nº papeis no mínimo de 1 mes')
    }

    # Initialize bottom for stacking
    bottom = pd.Series([0.0] * len(p1_raw), index=p1_raw.index)
    bar_width = 0.8

    # Plot stacked bars (reversed order so ATH is on top visually)
    for label_key in reversed(raw_cols):
        if label_key in plot_stuff:
            color, label = plot_stuff[label_key]
            ax1_twin.bar(
                p1_raw.index,
                p1_raw[label_key],
                label=label,
                color=color,
                alpha=0.7,
                width=bar_width,
                bottom=bottom,
            )
            bottom += p1_raw[label_key]

    ax1_twin.set_title(
        f"{idx} - Nº de novos máximos e novos mínimos - {start_date} a {end_date}",
        fontsize=12
    )
    ax1_twin.set_ylabel(f'% papéis ({ps.num_tickers} total)')
    ax1_twin.grid(True, linestyle='--', alpha=0.7)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines_twin1, labels_twin1 = ax1_twin.get_legend_handles_labels()

    ax1_twin.legend(
        lines1 + lines_twin1,
        labels1 + labels_twin1,
        loc='upper left',
        bbox_to_anchor=(0.01, 0.99)
    )

    #########################################################################
    # SUBPLOT 2: Highs minus Lows (Net Differences)
    #########################################################################

    ax2.set_title(
        f"{idx} - Nº novos máximos menos novos mínimos - {start_date} a {end_date}",
        fontsize=12
    )
    ax2.set_ylabel(f'{idx} preço')
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Apply x-axis formatting using PlotSetup
    ps.apply_xaxis(ax2)
    ax2.set_xlabel('Data')

    # Plot price on left axis
    ax2.plot(ps.plot_index, p_idx, color='black', linestyle='-',
             linewidth=2, label=f'{idx}', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor='black')

    # Create twin axis for bars
    ax2_twin = ax2.twinx()

    # Initialize bottom for stacking
    bottom = pd.Series([0.0] * len(p2), index=p2.index)

    # Plot stacked difference bars
    for i, column in enumerate(diff_cols):
        ax2_twin.bar(
            p2.index,
            p2[column],
            label=column,
            alpha=0.7,
            width=bar_width,
            bottom=bottom,
        )
        bottom += p2[column]

    ax2_twin.set_ylabel('Nº altos menos Nº baixos')

    # Combine legends
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines_twin2, labels_twin2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(
        lines2 + lines_twin2,
        labels2 + labels_twin2,
        loc='upper left',
        bbox_to_anchor=(0.01, 0.99)
    )

    return fig


# ============================================================================
# Main for testing
# ============================================================================
if __name__ == "__main__":
    from core.constants import file_locations
    from core.my_data_types import load_file_locations_dict, Config
    from datetime import datetime
    from main_modules.update_or_create import update_or_create_databases
    from utils.align_dataframes import align_and_prepare_for_plot
    from plotting.common_plot_setup import prepare_plot_data
    from indicators.hi_lo_indicators import calculate_highs_and_lows

    # Load file locations
    fileloc = load_file_locations_dict(file_locations)

    # Create test config
    cfg = Config(
        to_do=5,
        market_to_study={13: {'idx_code': '^BVSP', 'market': '3 ticker test',
                              'codes_csv': 'TEST.csv', "number_tickers": 3}},
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

    # Prepare plot setup
    ps = prepare_plot_data(index_df, components_df, cfg)

    # Calculate indicator
    hl_result = calculate_highs_and_lows(components_df)

    # Create plot
    fig = plot_highs_and_lows(ps, hl_result)
    plt.show()