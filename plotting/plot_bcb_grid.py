import matplotlib.pyplot as plt
import pandas as pd

from core.my_data_types import PlotSetup
from core.bcb_config import BCB_SHORT_BY_LONG

def plot_bcb_grid(
    ps: PlotSetup,
    df_bcb_daily: pd.DataFrame,
    usd_series: pd.Series | None = None,
    nrows: int = 3,
    ncols: int = 2,
):
    """
    Fixed version:
    - NO sharex=True (prevents Matplotlib from messing with bottom labels)
    - Explicit xticks everywhere
    - Only bottom-most used row shows labels
    """

    # 1) Align BCB data to IBOV dates
    idx = ps.price_data.index
    df_bcb_sample = df_bcb_daily.reindex(idx)

    # Smooth USD series (preferred)
    if usd_series is not None:
        usd_aligned = usd_series.reindex(idx)
        usd_vals = usd_aligned.values
    else:
        usd_vals = None

    # Exclude BCB USD series (we use Yahoo USD)
    usd_col_full = "BRL/USD Exchange Rate – End of period (commercial rate)"
    series_names = [c for c in df_bcb_sample.columns if c != usd_col_full]
    total_series = len(series_names)
    if total_series == 0:
        raise ValueError("df_bcb_daily has no BCB columns to plot (after excluding USD).")

    x = ps.plot_index
    adj = ps.price_data["Adj Close"].values

    # Left axis limits from IBOV only
    left_min = adj.min()
    left_max = adj.max()

    # Sparse tick positions
    full_positions = ps.tick_positions
    if not full_positions:
        sparse_positions = []
    else:
        sparse_positions = sorted(set(full_positions[::5] + [full_positions[-1]]))

    # Pre-build x-axis label text
    xlabels = [ps.date_labels[j] for j in sparse_positions]

    figs: list[plt.Figure] = []
    per_fig = nrows * ncols

    # ---------------------------
    # Loop over pages
    # ---------------------------
    for start in range(0, total_series, per_fig):
        end = min(start + per_fig, total_series)
        chunk = series_names[start:end]

        # ---- IMPORTANT CHANGE: sharex=False ----
        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(18, 9),
            sharex=False,
        )
        figs.append(fig)
        axes = axes.flatten()

        # Identify the last used row on THIS page
        last_used_index = len(chunk) - 1
        last_used_row = last_used_index // ncols

        bottom_row_axes = []

        # --------------------------------------------
        # Build EACH subplot
        # --------------------------------------------
        for i, col in enumerate(chunk):
            ax_left = axes[i]
            short = BCB_SHORT_BY_LONG.get(col, col)

            # Left axis: IBOV
            ax_left.plot(x, adj, color="black", linewidth=1.3, label=ps.idx)
            ax_left.fill_between(x, adj, color="lightgrey", alpha=0.4)
            ax_left.set_ylim(left_min, left_max)
            ax_left.set_ylabel("Adj Close / USD (scaled)", fontsize=8)
            ax_left.tick_params(axis="y", labelsize=8)
            ax_left.grid(True, axis="x", linestyle="-", alpha=0.3, color="gray", linewidth=0.8)

            # Left axis: USD (scaled to IBOV)
            if usd_vals is not None:
                usd_min = usd_vals.min()
                usd_max = usd_vals.max()
                if usd_max != usd_min:
                    usd_scaled = (usd_vals - usd_min) / (usd_max - usd_min)
                    usd_plot = left_min + usd_scaled * (left_max - left_min)
                else:
                    usd_plot = usd_vals * 0.0 + (left_min + left_max) / 2.0

                ax_left.plot(x, usd_plot, color="green", linewidth=1.0, label="BRL=X")
                ax_left.fill_between(x, usd_plot, color="green", alpha=0.15)

            # Right axis — one BCB series
            ax_right = ax_left.twinx()
            ax_right.plot(
                x,
                df_bcb_sample[col].values,
                linewidth=1.2,
                color="tab:blue",
                label=short,
            )
            ax_right.set_ylabel(short, fontsize=8)
            ax_right.tick_params(axis="y", labelsize=8)

            # Explicit xticks everywhere (otherwise set_xticklabels fails)
            ax_left.set_xticks(sparse_positions)

            # But hide labels for now (we fix bottom row after loop)
            ax_left.tick_params(axis="x", labelbottom=False)

            # Title
            ax_left.set_title(f"{ps.idx}, BRL=X vs " + r"$\mathbf{" + short + "}$", fontsize=10)

            # Legend
            h_left, l_left = ax_left.get_legend_handles_labels()
            h_right, l_right = ax_right.get_legend_handles_labels()
            ax_left.legend(
                h_left + h_right,
                l_left + l_right,
                loc="upper left",
                fontsize=7,
            )

            # Track bottom-most *used* row axes
            if (i // ncols) == last_used_row:
                bottom_row_axes.append(ax_left)

        # Hide unused axes
        for j in range(len(chunk), per_fig):
            axes[j].set_visible(False)

        # ---------------------------------------------------
        # Finally: SHOW labels only on bottom-most used row
        # ---------------------------------------------------
        for ax in bottom_row_axes:
            ax.tick_params(axis="x", labelbottom=True)
            ax.set_xticklabels(xlabels, rotation=45, fontsize=8)

        """fig.suptitle(
            f"{ps.idx} vs BCB indicators (raw, {len(chunk)} series)",
            fontsize=14,
        )"""

    return figs


