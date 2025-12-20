import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.my_data_types import PlotSetup


def plot_breadth_breakout(df_in: pd.DataFrame, ps: PlotSetup) -> plt.Figure:
    """
    Breakout-oriented breadth dashboard.

    Panels (top → bottom):
    1) ZBT (ignition)
    2) McClellan Oscillator (acceleration)
    3) McClellan Summation Index (regime)
    4) Cumulative Advance / Decline (confirmation)
    """

    #df = df_in.tail(ps.lookback_period).copy()
    df = df_in.loc[ps.price_data.index].copy()

    zbt = df['ZBT']
    thrust = df['ZBT_thrust']
    mcc = df['McClellan_Oscillator']
    msi = df['McClellan_Summation']
    ad_cum = df['A/D_cum_diff']

    fig, axs = plt.subplots(
        nrows=4,
        ncols=1,
        figsize=(18, 9),
        sharex=True
    )

    # ------------------------------------------------------------
    # 1. ZBT — Ignition
    # ------------------------------------------------------------
    axs[0].set_title(f"{ps.mkt} — Zweig Breadth Thrust (Ignition: %age of mkt participating)", fontsize=12, fontweight='bold')
    ps.plot_price_layer(axs[0])
    ax_r0 = axs[0].twinx()

    #ax_r0.plot(ps.plot_index, zbt, linewidth=1.6, label='ZBT')
    ax_r0.plot(ps.plot_index, zbt, linewidth=1.6, label='ZBT')
    ax_r0.axhline(0.40, linestyle='--', linewidth=1.2)
    ax_r0.axhline(0.615, linestyle='--', linewidth=1.2)

    axs[0].grid(True, alpha=0.3)
    ax_r0.set_ylabel('ZBT')
    ax_r0.legend(loc="upper left", fontsize=8, frameon=True)

    # ------------------------------------------------------------
    # 2. McClellan Oscillator — Acceleration
    # ------------------------------------------------------------
    axs[1].set_title(f"{ps.mkt} — McClellan Oscillator (Acceleration, speed of change)", fontsize=12)
    ps.plot_price_layer(axs[1])
    ax_r1 = axs[1].twinx()

    colors = np.where(mcc > 0, 'green', np.where(mcc < 0, 'red', 'gray'))
    ax_r1.bar(ps.plot_index, mcc, color=colors, alpha=0.7, label='McClellan Osc')
    ax_r1.axhline(0, linestyle='--', linewidth=1.2)
    ax_r1.set_ylabel('McClellan Osc.')


    axs[1].grid(True, alpha=0.3)
    ax_r1.legend(loc="upper left", fontsize=8, frameon=True)

    # ------------------------------------------------------------
    # 3. McClellan Summation Index — Regime
    # ------------------------------------------------------------
    axs[2].set_title(f"{ps.mkt} — McClellan Summation Index (Intermediate/Trend Following)", fontsize=12)
    ps.plot_price_layer(axs[2])
    ax_r2 = axs[2].twinx()

    ax_r2.plot(ps.plot_index, msi, linewidth=1.6, label='MSI')
    ax_r2.axhline(0, linestyle='--', linewidth=1.2)
    ax_r2.set_ylabel('MSI')


    axs[2].grid(True, alpha=0.3)
    ax_r2.legend(loc="upper left", fontsize=8, frameon=True)

    # ------------------------------------------------------------
    # 4. Cumulative A/D — Confirmation
    # ------------------------------------------------------------
    axs[3].set_title(f"{ps.mkt} — Cumulative Advance/Decline (Confirmation, measure mkt participation"
                     f")", fontsize=12)
    ps.plot_price_layer(axs[3])
    ax_r3 = axs[3].twinx()

    ax_r3.plot(ps.plot_index, ad_cum, linewidth=1.6, label='Adv − Dec')
    ax_r3.axhline(0, linestyle='--', linewidth=1.2)
    ax_r3.set_ylabel('Cum. advance/decline')

    axs[3].grid(True, alpha=0.3)
    ax_r3.legend(loc="upper left", fontsize=8, frameon=True)

    # X-axis formatting
    ps.apply_xaxis(axs[3])

    # Remove white padding on left and right edges of plots
    for ax in axs:
        ax.set_xmargin(0)

    return fig
