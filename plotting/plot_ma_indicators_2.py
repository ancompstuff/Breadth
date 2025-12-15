import matplotlib.pyplot as plt
from utils.build_color_map import mka_color_map


def plot_vwma_percent_trends_3panels(
    ps,
    df_trends
):
    """
    Plot VWMA trend participation (% only) with price on left axis.

    Left axis  : Adj Close (PlotSetup)
    Right axis : %>VWMA trend combinations
    """

    df_trends = df_trends.tail(ps.lookback_period)

    fig, axes = plt.subplots(
        nrows=3,
        ncols=1,
        figsize=(18, 9),
        sharex=True
    )

    panels = {
        "Short term":  ["VWMA5", "VWMA5&12", "VWMA5&12&25"],
        "Medium term": ["VWMA40", "VWMA40&60", "VWMA40&60&80"],
        "Long term":   ["VWMA50", "VWMA50&100", "VWMA50&100&200"],
    }

    for ax, (title, combos) in zip(axes, panels.items()):

        # --------------------------------------------------
        # Left axis: price (mandatory, always)
        # --------------------------------------------------
        ps.plot_price_layer(ax)

        # --------------------------------------------------
        # Right axis: percent trends only
        # --------------------------------------------------
        ax_r = ax.twinx()

        for label in combos:
            pct_col = f"%>{label}"

            ax_r.plot(
                ps.plot_index,
                df_trends[pct_col].values,
                color=mka_color_map[pct_col],
                linewidth=1.6,
                label=pct_col,
                zorder=5
            )

        # --------------------------------------------------
        # Formatting
        # --------------------------------------------------
        ax.set_title(title, fontsize=10)
        ax_r.set_ylabel("% do índice", fontsize=8)
        ax_r.set_ylim(0, 100)

        ax.grid(True, axis="y", alpha=0.3)
        ps.fix_xlimits(ax)

    # ------------------------------------------------------
    # X-axis formatting once (bottom)
    # ------------------------------------------------------
    ps.apply_xaxis(axes[-1])

    fig.suptitle(
        f"{ps.idx} – VWMA Trend Participation (%) "
        f"({ps.sample_start} → {ps.sample_end})",
        fontsize=12
    )

    #plt.tight_layout()
    #plt.show()
