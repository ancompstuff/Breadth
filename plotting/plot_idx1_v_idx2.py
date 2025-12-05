import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

from indicators.get_idx1_idx2 import get_idx1_idx2


def plot_idx1_v_idx2(idx1, idx2, config, fileloc, plot_setup):
    """
    Final version:
        • Subplot 1 = IBOV (left) + idx2 (right) + correlation (far-right)
        • Subplot 2 = IBOV (left) + SELIC% (right)
        • Subplot 3 = IBOV (left) + IPCA%  (right)
        • All share x-axis (labels only on bottom)
        • Legends top-left
    """

    # ----------------------------------------------------------------------
    # Load all aligned data (IBOV, idx2, SELIC, IPCA)
    # ----------------------------------------------------------------------
    df = get_idx1_idx2(idx1, idx2, config, fileloc, plot_setup)
    df.index = pd.to_datetime(df.index)

    x = plot_setup.plot_index

    col_ibov = "IBOV"
    col_idx2 = idx2
    col_selic = "SELIC"
    col_ipca = "IPCA"

    # ----------------------------------------------------------------------
    # Prepare correlation
    # ----------------------------------------------------------------------
    corr_window = 20

    # rolling correlation on aligned series
    df["Correlation"] = (
        df[col_ibov]
        .rolling(corr_window)
        .corr(df[col_idx2])
    )

    # ----------------------------------------------------------------------
    # Axes
    # ----------------------------------------------------------------------
    fig, axs = plt.subplots(3, 1, figsize=(18, 9), sharex=True)
    ax_top, ax_selic, ax_ipca = axs

    # percentage formatter
    # percent_fmt = FuncFormatter(lambda y, _: f"{y*100:.1f}%")

    """# helper
    def draw_ibov(ax):
        plot_setup.plot_price_layer(ax)
        ax.legend(loc="upper left")

    draw_ibov(ax_top)"""

    plot_setup.plot_price_layer(ax_top)

    # idx2 on right
    ax_r = ax_top.twinx()
    ax_r.plot(x, df[col_idx2].values, color="green", linewidth=1.2, label=idx2)
    ax_r.set_ylabel(idx2, color="green")
    ax_r.tick_params(axis='y', labelcolor="green")

    # correlation on FAR right
    ax_corr = ax_top.twinx()
    ax_corr.spines["right"].set_position(("outward", 50))
    ax_corr.plot(x, df["Correlation"].values, color="blue", linewidth=1.3, label="Corr 20d")
    ax_corr.set_ylabel("Correlation", color="blue")
    ax_corr.tick_params(axis='y', labelcolor="blue")
    ax_corr.set_ylim(-1.05, 1.05)
    ax_corr.axhline(0, color='blue', linestyle='--', linewidth=1)

    # ---- POSITIVE CORRELATION SHADING ----
    corr = df["Correlation"].values

    ax_corr.fill_between(
        x,
        0,
        corr,
        where=(corr > 0),
        color="green",
        alpha=0.25,
        interpolate=True,
        zorder=1
    )

    ax_top.set_title(f"{idx1} vs {idx2} + Correlation ({plot_setup.sample_start}-{plot_setup.sample_end})")
    ax_top.grid(True, axis='x', linestyle='--', alpha=0.4)
    #ax_top.legend(loc="upper left")

    # ---- MERGED LEGEND FOR 3 AXES ----
    handles, labels = [], []
    for ax in [ax_top, ax_r, ax_corr]:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)

    ax_corr.legend(handles, labels, loc="upper left")

    # ----------------------------------------------------------------------
    # 2) SELIC subplot
    # ----------------------------------------------------------------------
    #draw_ibov(ax_selic)
    plot_setup.plot_price_layer(ax_selic)

    ax_selic_r = ax_selic.twinx()
    ax_selic_r.plot(x, df[col_selic].values, linewidth=1.2, color="tab:blue", label="SELIC (% mensal)")
    ax_selic_r.set_ylabel("SELIC (% mensal)", color="tab:blue")
    ax_selic_r.tick_params(axis='y', labelcolor="tab:blue")
    #ax_selic_r.yaxis.set_major_formatter(percent_fmt)
    ax_selic_r.grid(True, axis='y', linestyle='--', alpha=0.4)

    ax_selic.set_title("SELIC vs IBOV")
    ax_selic.grid(True, axis='x', linestyle='--', alpha=0.4)
    #ax_selic.legend(loc="upper left")

    # ---- MERGED LEGEND FOR 2 AXES ----
    handles, labels = [], []
    for ax in [ax_selic, ax_selic_r]:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)

    ax_selic_r.legend(handles, labels, loc="upper left")

    # ----------------------------------------------------------------------
    # 3) IPCA subplot
    # ----------------------------------------------------------------------
    #draw_ibov(ax_ipca)
    plot_setup.plot_price_layer(ax_ipca)

    ax_ipca_r = ax_ipca.twinx()
    ax_ipca_r.plot(x, df[col_ipca].values, linewidth=1.2, color="tab:orange", label="IPCA (% mensal)")
    ax_ipca_r.set_ylabel("IPCA (% mensal)", color="tab:orange")
    ax_ipca_r.tick_params(axis='y', labelcolor="tab:orange")
    #ax_ipca_r.yaxis.set_major_formatter(percent_fmt)
    ax_ipca_r.grid(True, axis='y', linestyle='--', alpha=0.4)

    ax_ipca.set_title("IPCA vs IBOV")
    ax_ipca.grid(True, axis='x', linestyle='--', alpha=0.4)
    #ax_ipca.legend(loc="upper left")

    # ---- MERGED LEGEND FOR 2 AXES ----
    handles, labels = [], []
    for ax in [ax_ipca, ax_ipca_r]:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)

    ax_ipca_r.legend(handles, labels, loc="upper left")

    ax_top.set_title(f"{idx1} vs {idx2} + Correlation")
    ax_top.grid(True, axis='x', linestyle='--', alpha=0.4)

    # bottom subplot gets x-axis labels
    plot_setup.apply_xaxis(ax_ipca)

    #fig.tight_layout()
    return fig
