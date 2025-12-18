import matplotlib.pyplot as plt
import numpy as np


def plot_vwma_percent_trends_4panels(
    ps,
    ladder,      # <- main ladder (heatmap uses this)
    mini_ladders # <- mini ladders (subplots 1–3 use this)
):
    """
    Panels:
        1) Short mini ladder (s)
        2) Medium mini ladder (m)
        3) Long mini ladder (l)
        4) Heatmap: full main ladder (5 -> 200)
    """

    #ladder = ladder.tail(ps.lookback_period)  # does NOT guarantee that the dates match ps.price_data.index
    ladder = ladder.loc[ps.price_data.index]
    #mini_ladders = mini_ladders.tail(ps.lookback_period)
    mini_ladders = mini_ladders.loc[ps.price_data.index]

    fig, axes = plt.subplots(
        nrows=4,
        ncols=1,
        figsize=(18, 9),
        sharex=True
    )

    # -------------------------
    # Columns for panels 1–3
    # -------------------------
    short_cols = ["s$>V5%", "s$>V5>V12%", "s$>V5>V12>V25%"]
    medium_cols = ["m$>V40%", "m$>V40>50%", "m$>V40>50>60%"]
    long_cols = ["l$>V80%", "l$>V80>100%", "l$>V80>100>200%"]

    bar_labels = {
        short_cols[0]: "$>VWMA5 (%)",
        short_cols[1]: "$>VWMA5>12 (%)",
        short_cols[2]: "$>VWMA5>12>25 (%)",

        medium_cols[0]: "$>VWMA40 (%)",
        medium_cols[1]: "$>VWMA40>50 (%)",
        medium_cols[2]: "$>VWMA40>50>60 (%)",

        long_cols[0]: "$>VWMA80 (%)",
        long_cols[1]: "$>VWMA80>100 (%)",
        long_cols[2]: "$>VWMA80>100>200 (%)",
    }

    colors = ["#d62728", "#ff7f0e", "#2ca02c"]

    panels = [
        ("Short-term ladder", short_cols),
        ("Medium-term ladder", medium_cols),
        ("Long-term ladder", long_cols),
    ]

    # -------------------------
    # First 3 panels (mini_ladders)
    # -------------------------
    for ax, (title, cols) in zip(axes[:3], panels):
        ps.plot_price_layer(ax)
        ax_r = ax.twinx()

        for c, col in zip(colors, cols):
            ax_r.bar(
                ps.plot_index,
                mini_ladders[col].values,
                color=c,
                alpha=0.6,
                label=bar_labels[col],
                zorder=5
            )

        ax.set_title(title, fontsize=10)
        ax_r.set_ylabel("% of tickers", fontsize=8)
        ax_r.set_ylim(0, 100)

        ax.grid(True, axis="y", alpha=0.3)
        ps.fix_xlimits(ax)
        ax_r.legend(loc="upper left", fontsize=8, frameon=True)

    # -------------------------
    # Heatmap (main ladder)
    # -------------------------
    ax_hm = axes[3]

    heat_cols = [
        "$>V5%",
        "$>V5>V12%",
        "$>V5>V12>V25%",
        "$>V5>V12>V25>V40%",
        "$>V5>V12>V25>V40>V50%",
        "$>V5>V12>V25>V40>V50>V60%",
        "$>V5>V12>V25>V40>V50>V60>V80%",
        "$>V5>V12>V25>V40>V50>V60>V80>V100%",
        "$>V5>V12>V25>V40>V50>V60>V80>V100>V200%",
    ]

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

    missing = [c for c in heat_cols if c not in ladder.columns]
    if missing:
        raise KeyError(f"Missing expected ladder columns for heatmap: {missing}")

    heat_data = ladder[heat_cols].T.values

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
        fontsize=12,
        fontweight='bold'
    )

    return fig