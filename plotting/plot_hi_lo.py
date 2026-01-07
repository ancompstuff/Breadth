"""
Highs and Lows Plotting
=======================
Creates dual-panel visualization:
1. Top panel: Stacked bars of highs/lows counts (normalized to %) + index overlay
2. Bottom panel: Stacked bars of net differences (normalized to %) + index overlay
"""

import pandas as pd
import matplotlib.pyplot as plt

from core.my_data_types import PlotSetup
from core.constants import RAW_COUNT_COLS, DIFF_COUNT_COLS, HI_LO_PLOT_CONFIG


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
    num_tickers = ps.num_tickers  # Total number of stocks

    # Slice data based on lookback for plotting
    p = hl_df.iloc[-lookback:]

    # Reset index to integer for plotting
    p_indexed = p.reset_index()
    date_labels = p_indexed['Date'].dt.strftime("%d/%m/%y").tolist()
    p1 = p_indexed.drop(columns=['Date'])

    # --- 1) NORMALIZAÇÃO PARA PORCENTAGEM (Subplots 1 e 2) ---

    # Extract, filter, and normalize the raw count columns
    p1_raw = p1[RAW_COUNT_COLS]
    p1_raw_norm = (p1_raw / num_tickers) * 100

    # Extract, filter, and normalize the difference columns
    p2_raw = p1[DIFF_COUNT_COLS]
    p2_norm = (p2_raw / num_tickers) * 100

    # Get price data (already sliced in ps)
    p_idx = ps.price_data['Adj Close'].values

    #########################################################################
    # CREATE FIGURE
    #########################################################################
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 9), sharex=True)

    start_date = p.index[0].strftime('%d/%m/%y')
    end_date = p.index[-1].strftime('%d/%m/%y')

    #########################################################################
    # SUBPLOT 1: Highs and Lows Counts (Normalized %)
    #########################################################################

    # Plot price on left axis
    ax1.plot(ps.plot_index, p_idx, color='black', linestyle='-',
             linewidth=2, label=f'{idx}', alpha=0.7)
    ax1.set_ylabel(f'{idx} preço')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, axis='x', alpha=0.7)


    # Create twin axis for bars
    ax1_twin = ax1.twinx()

    # Define the order of bars for plotting (reversed so ATH/ATL are on top)
    # We use RAW_COUNT_COLS and HI_LO_PLOT_CONFIG

    # Initialize bottom for stacking
    bottom = pd.Series([0.0] * len(p1_raw_norm), index=p1_raw_norm.index)
    bar_width = 0.8

    # --- 3) IMPLEMENTAÇÃO DO GRADIENTE DE CORES (Subplot 1) ---
    # Plot stacked bars (reversed order for better visual stacking)
    for label_key in reversed(RAW_COUNT_COLS):
        if label_key in HI_LO_PLOT_CONFIG:
            config = HI_LO_PLOT_CONFIG[label_key]
            color, label = config['color'], config['label']
            ax1_twin.bar(
                p1_raw_norm.index,
                p1_raw_norm[label_key],  # Usando dados normalizados
                label=label,
                color=color,
                alpha=0.7,
                width=bar_width,
                bottom=bottom,
            )
            bottom += p1_raw_norm[label_key]

    ax1_twin.set_title(
        f"{idx} - % de novos máximos e novos mínimos - {start_date} a {end_date}",
        fontsize=12
    )
    # Rótulo de eixo atualizado
    ax1_twin.set_ylabel('Stacked % de ativos')
    ax1_twin.grid(True, axis='y', alpha=0.7)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines_twin1, labels_twin1 = ax1_twin.get_legend_handles_labels()

    ax1_twin.legend(
        lines1 + lines_twin1,
        labels1 + labels_twin1,
        loc='upper left',
        bbox_to_anchor=(0.01, 0.99),
        framealpha=0.8,
        facecolor='white'
    )

    #########################################################################
    # SUBPLOT 2: Highs minus Lows (Net Differences - Normalized %)
    #########################################################################

    ax2.set_title(
        f"{idx} - % novos máximos menos novos mínimos",
        fontsize=12
    )
    ax2.set_ylabel(f'{idx} preço')
    ax2.grid(True, axis='x', alpha=0.7)

    # Apply x-axis formatting using PlotSetup
    ps.apply_xaxis(ax2)
    ax2.set_xlabel('Data')

    # Plot price on left axis
    ax2.plot(ps.plot_index, p_idx, color='black', linestyle='-',
             linewidth=2, label=f'{idx}', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor='black')

    # Create twin axis for bars
    ax2_twin = ax2.twinx()

    # --- 2) CÁLCULO E MARCAÇÃO DE EXTREMOS (10º e 90º Percentis) ---
    # O total_diff representa a soma de todas as diferenças normalizadas (eixos da barra)
    total_diff = p2_norm.sum(axis=1)
    p90 = total_diff.quantile(0.9)
    p10 = total_diff.quantile(0.1)

    # Adiciona as linhas de percentil
    ax2_twin.axhline(p90, color='darkorange', linestyle='--', linewidth=1.5, alpha=0.8,
                     label=f'90º Percentil ({p90:.2f}%)')
    ax2_twin.axhline(p10, color='darkblue', linestyle='--', linewidth=1.5, alpha=0.8,
                     label=f'10º Percentil ({p10:.2f}%)')

    # Initialize bottom for stacking
    bottom = pd.Series([0.0] * len(p2_norm), index=p2_norm.index)

    # Plot stacked difference bars
    for i, column in enumerate(DIFF_COUNT_COLS):
        # Cores para as diferenças: Alto-Baixo Histórico/12M/3M/1M
        color = ['purple', 'darkcyan', 'mediumblue', 'steelblue'][i]

        ax2_twin.bar(
            p2_norm.index,
            p2_norm[column],  # Usando dados normalizados
            label=column,
            color=color,
            alpha=0.7,
            width=bar_width,
            bottom=bottom,
        )
        bottom += p2_norm[column]

    # Rótulo de eixo atualizado
    ax2_twin.set_ylabel('Stacked % de ativos (Altos - Baixos)')

    ax2_twin.grid(True, axis='y', alpha=0.7)

    # Combine legends
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines_twin2, labels_twin2 = ax2_twin.get_legend_handles_labels()
    ax2_twin.legend(
        lines2 + lines_twin2,
        labels2 + labels_twin2,
        loc='upper left',
        bbox_to_anchor=(0.01, 0.99),
        framealpha=0.8,
        facecolor='white'
    )


    return fig


# ============================================================================
# Main for testing (mantido inalterado)
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
    #plt.show()
