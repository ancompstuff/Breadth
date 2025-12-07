import matplotlib.pyplot as plt
import pandas as pd

from core.my_data_types import PlotSetup
from core.bcb_config import BCB_SHORT_BY_LONG


def plot_bcb_vs_yahoo(ps: PlotSetup, df_bcb_daily: pd.DataFrame):
    """
    Plot IBOV Adj Close on the left axis (raw, not normalized),
    and all BCB series on the right axis, normalized to 100 at
    the start of the sample window defined by PlotSetup.

    Parameters
    ----------
    ps : PlotSetup
        Created by plotting.common_plot_setup.prepare_plot_data.
        - ps.price_data.index defines the daily sample window
        - ps.plot_index, ps.date_labels, ps.tick_positions shape the x-axis

    df_bcb_daily : pd.DataFrame
        DAILY BCB data, already forward-filled to at least the IBOV calendar.
        Index: DatetimeIndex (at least covering ps.price_data.index).
        Columns: one column per BCB indicator (e.g. SELIC, IPCA, etc.).
    """

    # ------------------------------------------------------------------
    # 1) Align BCB data to the sample window used by PlotSetup
    # ------------------------------------------------------------------
    idx = ps.price_data.index              # datetime index for the sample
    df_bcb_sample = df_bcb_daily.reindex(idx)

    # ------------------------------------------------------------------
    # 2) Scale each BCB series to its own [min, max] over the sample
    #     → values in [0, 100] for the right axis
    # ------------------------------------------------------------------
    df_bcb_norm = df_bcb_sample.copy()

    for col in df_bcb_norm.columns:
        series = df_bcb_norm[col]
        s_min = series.min()
        s_max = series.max()

        if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
            # cannot scale a constant or empty series
            df_bcb_norm[col] = pd.NA
        else:
            df_bcb_norm[col] = 100.0 * (series - s_min) / (s_max - s_min)

    df_bcb_norm = df_bcb_norm.dropna(axis=1, how="all")
    if df_bcb_norm.empty:
        raise ValueError("No BCB series could be scaled for this sample window.")

    # ------------------------------------------------------------------
    # 3) Create figure and axes, using PlotSetup conventions
    # ------------------------------------------------------------------

    fig, ax_left = plt.subplots(figsize=(18, 9))  # NO tight_layout here

    # Left axis: raw Adj Close (from PlotSetup)
    adj = ps.price_data["Adj Close"].values
    x = ps.plot_index

    ax_left.plot(
        x,
        adj,
        color="black",
        linewidth=1.5,
        label=ps.idx,           # e.g. "^BVSP"
    )
    ax_left.fill_between(x, adj, color="lightgrey", alpha=0.4)
    ax_left.set_ylim(ps.ymin, ps.ymax)
    ax_left.set_ylabel("Adj Close", color="black")
    ax_left.tick_params(axis="y", labelcolor="black")

    # Vertical grid like other plots
    ax_left.grid(True, axis="both", linestyle="-", alpha=0.3, color="gray", linewidth=0.8)

    # ------------------------------------------------------------------
    # 4) Right axis: normalized BCB series
    # ------------------------------------------------------------------
    ax_right = ax_left.twinx()

    for col in df_bcb_norm.columns:
        # map time index to numeric plot_index
        ax_right.plot(
            x,
            df_bcb_norm[col].values,
            linewidth=1.2,
            label=col,
        )

    ax_right.set_ylabel("BCB indicators (0–100: scaled to own min/max)")
    ax_right.tick_params(axis="y")

    # ------------------------------------------------------------------
    # 5) X‑axis labelling using PlotSetup
    # ------------------------------------------------------------------
    # Use ps.tick_positions on numeric x-axis
    ax_left.set_xticks(ps.tick_positions)
    ax_left.set_xticklabels(
        [ps.date_labels[i] for i in ps.tick_positions],
        rotation=45,
        fontsize=8,
    )

    # ------------------------------------------------------------------
    # 6) Title and legend
    # ------------------------------------------------------------------
    title = f"{ps.idx} vs BCB indicators (normalized at {ps.sample_start})"
    ax_left.set_title(title, fontsize=14)

    # Legend on the LEFT side, merged from both axes
    handles_left, labels_left = ax_left.get_legend_handles_labels()
    handles_right, labels_right = ax_right.get_legend_handles_labels()

    all_handles = handles_left + handles_right
    all_labels = labels_left + labels_right

    ax_left.legend(all_handles, all_labels, loc="upper left")

    return fig, (ax_left, ax_right)