import matplotlib.pyplot as plt
import numpy as np


def plot_vwma_percent_trends_4panels(
    ps,
    df_trends,   # unused, kept for API stability
    df_ladder,
):
    """
    Plot TRUE VWMA ladder participation (%).

    Panels:
        1) Short ladder  (ends at 25)
        2) Medium ladder (ends at 40–60)
        3) Long ladder   (ends at 80–200)
        4) Heatmap: full ladder
    """

    df_ladder = df_ladder.tail(ps.lookback_period)
    print(df_ladder.columns)

    fig, axes = plt.subplots(
        nrows=4,
        ncols=1,
        figsize=(18, 9),
        sharex=True
    )

    # ------------------------------------------------------------------
    # CORRECT ladder columns (EXISTING)
    # ------------------------------------------------------------------
    short_cols = [
        "$>V5",
        "$>V5>V12",
        "$>V5>V12>V25",
    ]

    medium_cols = [
        "$>V5>V12>V25>V40",
        "$>V5>V12>V25>V40>V50",
        "$>V5>V12>V25>V40>V50>V60",
    ]

    long_cols = [
        "$>V5>V12>V25>V40>V50>V60>V80",
        "$>V5>V12>V25>V40>V50>V60>V80>V100",
        "$>V5>V12>V25>V40>V50>V60>V80>V100>V200",
    ]

    bar_labels = {
        short_cols[0]: "$>VWMA5 (%)",
        short_cols[1]: "$>VWMA5>12 (%)",
        short_cols[2]: "$>VWMA5>12>25 (%)",

        medium_cols[0]: "$>VWMA5–40 (%)",
        medium_cols[1]: "$>VWMA5–50 (%)",
        medium_cols[2]: "$>VWMA5–60 (%)",

        long_cols[0]: "$>VWMA5–80 (%)",
        long_cols[1]: "$>VWMA5–100 (%)",
        long_cols[2]: "$>VWMA5–200 (%)",
    }

    colors = ["#d62728", "#ff7f0e", "#2ca02c"]

    panels = [
        ("Short-term ladder", short_cols),
        ("Medium-term ladder", medium_cols),
        ("Long-term ladder", long_cols),
    ]

    # ------------------------------------------------------------------
    # First 3 panels
    # ------------------------------------------------------------------
    for ax, (title, cols) in zip(axes[:3], panels):

        ps.plot_price_layer(ax)
        ax_r = ax.twinx()

        for c, col in zip(colors, cols):
            ax_r.bar(
                ps.plot_index,
                df_ladder[col].values,
                color=c,
                alpha=0.85,
                label=bar_labels[col],
                zorder=5
            )

        ax.set_title(title, fontsize=10)
        ax_r.set_ylabel("% of tickers", fontsize=8)
        ax_r.set_ylim(0, 100)

        ax.grid(True, axis="y", alpha=0.3)
        ps.fix_xlimits(ax)
        ax_r.legend(loc="upper left", fontsize=8, frameon=True)

    # ------------------------------------------------------------------
    # Heatmap — FULL ladder (already correct)
    # ------------------------------------------------------------------
    ax_hm = axes[3]

    heat_cols = list(df_ladder.columns)

    heat_labels = [
        "$>VWMA5 ladder",
        "$>VWMA5–12 ladder",
        "$>VWMA5–25 ladder",
        "$>VWMA5–40 ladder",
        "$>VWMA5–50 ladder",
        "$>VWMA5–60 ladder",
        "$>VWMA5–80 ladder",
        "$>VWMA5–100 ladder",
        "$>VWMA5–200 ladder",
    ]

    heat_data = df_ladder[heat_cols].T.values

    ax_hm.imshow(
        heat_data,
        aspect="auto",
        cmap="hot",
        vmin=0,
        vmax=100
    )

    ax_hm.set_yticks(np.arange(len(heat_labels)))
    ax_hm.set_yticklabels(heat_labels, fontsize=8)
    ax_hm.set_title("VWMA Structural Ladder (%)", fontsize=10)

    ps.apply_xaxis(ax_hm)

    fig.suptitle(
        f"{ps.idx} – VWMA Structural Participation (%) "
        f"({ps.sample_start} → {ps.sample_end})",
        fontsize=12
    )

    return fig
