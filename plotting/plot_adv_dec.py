import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.my_data_types import PlotSetup


def plot_advance_decline(ps: PlotSetup, df_in: pd.DataFrame) -> plt.Figure:
    """
    Plot advance/decline indicators:  TRIN, cumulative A/D, and McClellan Oscillator.

    Args:
        ps: PlotSetup dataclass containing plot configuration
        df_in: DataFrame from calculate_advance_decline() with indicator columns

    Returns:
        matplotlib Figure object
    """
    # Align to plot setup date range
    df_t0_plot = df_in.loc[ps.price_data.index].copy()

    pidx = df_t0_plot['idx_close']
    p1 = df_t0_plot['TRIN']
    p2 = df_t0_plot['TRIN'].rolling(window=5).mean()
    p3 = df_t0_plot['A/D_cum_diff']
    p4 = df_t0_plot['McClellan_Oscillator']

    # Create figure with 3 subplots
    fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(18, 9), sharex=True)

    ##################################
    # Plot 1: TRIN vs Index
    ##################################
    axs[0].set_title(
        f"{ps.mkt} - TRIN (NºAdv/NºDec) / (Adv vol/Dec vol) :  {ps.sample_start} - {ps.sample_end}",
        fontsize=12, fontweight='bold'
    )
    ps.plot_price_layer(axs[0])
    axs[0].grid(True, alpha=0.3)

    ax_r0 = axs[0].twinx()
    ax_r0.plot(ps.plot_index, p1, color='green', alpha=0.7,
                label='TRIN :  <1 = bullish; >1 = bearish; 1 = neutro')
    ax_r0.plot(ps.plot_index, p2, color='red', alpha=0.7, label='5d Movong average do TRIN')
    ax_r0.axhline(y=1, color='gray', linestyle='dotted', linewidth=1.5, label = 'Nível Neutro (1.0)')

    ax_r0.set_ylabel('TRIN')
    ax_r0.tick_params(axis='y', labelsize=6)
    ax_r0.grid(True, axis='x', linestyle='--', alpha=0.7)

    lines, labels = axs[0].get_legend_handles_labels()
    lines2, labels2 = ax_r0.get_legend_handles_labels()
    ax_r0.legend(lines + lines2, labels + labels2, loc='upper left')

    ########################
    # Plot 2: A/D cumulative
    ########################
    axs[1].set_title(
        f'{ps.mkt} - Cumulativo de papeis avançando menos papeis declinando',
        fontsize=12
    )
    ps.plot_price_layer(axs[1])
    axs[1].grid(True, alpha=0.3)

    ax_r1 = axs[1].twinx()

    ax_r1.plot(ps.plot_index, p3, color='b', alpha=0.7, label='Cumulativo (subindo - caindo)')
    ax_r1.set_ylabel('Cumulative (Adv - Dec)', color='black')

    valid_values = p3[~np.isnan(p3) & ~np.isinf(p3)]
    if len(valid_values) > 0:
        ax_r1.set_ylim(bottom=min(valid_values), top=max(valid_values))
    ax_r1.tick_params(axis='y', labelsize=6)
    ax_r1.axhline(y=0, color='blue', linestyle='--', linewidth=1.5)
    ax_r1.grid(True, axis='x', linestyle='--', alpha=0.7)


    lines, labels = axs[1].get_legend_handles_labels()
    lines2, labels2 = ax_r1.get_legend_handles_labels()
    ax_r1.legend(lines + lines2, labels + labels2, loc='upper left')

    ##############################
    # Plot 3: McClellan Oscillator
    ##############################
    axs[2].set_title(
        f'{ps.mkt} - Oscilador McClellan (>0 = dinheiro entrando, <0 = dinheiro saindo)',
        fontsize=12
    )
    ps.plot_price_layer(axs[2])
    ax_r2= axs[2].twinx()

    colors = ['green' if val > 0 else 'red' for val in p4]
    ax_r2.bar(ps.plot_index, p4, color=colors, alpha=0.7, label='Oscilador McClellan')
    ax_r2.set_ylabel('Oscilador McClellan', color='black')
    ax_r2.tick_params(axis='y', labelsize=6)
    ax_r2.axhline(y=0, color='blue', linestyle='--', linewidth=1.5)

    axs[2].grid(True, alpha=0.3)

    lines, labels = axs[2].get_legend_handles_labels()
    lines2, labels2 = ax_r2.get_legend_handles_labels()
    ax_r2.legend(lines + lines2, labels + labels2, loc='upper left')

    ps.apply_xaxis(axs[2])

    return fig