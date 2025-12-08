import os
import pandas as pd
import matplotlib.pyplot as plt
from core.constants import yahoo_market_details


def load_index_adj_close(idx_code: str, fileloc) -> pd.Series:
    path = os.path.join(fileloc.yahoo_downloaded_data_folder, f"INDEX_{idx_code}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing index file: {path}")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df[~df.index.duplicated(keep="first")]
    if "Adj Close" not in df.columns:
        raise ValueError(f"Adj Close column missing for index {idx_code}")
    return df["Adj Close"].sort_index()


def plot_bvsp_vs_all_indices(ps, fileloc, nrows=3, ncols=2):
    bvsp = ps.price_data["Adj Close"].copy()
    idx_dates = bvsp.index
    figs = []
    per_fig = nrows * ncols
    # Use all yahoo_market_details entries EXCEPT BVSP
    other_indices = [info for info in yahoo_market_details.values()
                     if info.get("idx_code") not in ("^BVSP", None)]

    # Sparse tick positions
    full_positions = ps.tick_positions
    if not full_positions:
        sparse_positions = []
    else:
        # Select sparse positions (every 5th position plus the last)
        sparse_positions = sorted(set(full_positions[::5] + [full_positions[-1]]))

    # Pre-build x-axis label text
    xlabels = [ps.date_labels[j] for j in sparse_positions]

    # Plot each chunk
    for start in range(0, len(other_indices), per_fig):
        end = min(start + per_fig, len(other_indices))
        chunk = other_indices[start:end]
        fig, axes = plt.subplots(
            nrows=nrows, ncols=ncols,
            figsize=(18, 9),
            sharex=False
        )
        axes = axes.flatten()

        for ax, market_info in zip(axes, chunk):
            code = market_info["idx_code"]
            series = load_index_adj_close(code, fileloc)
            series = series.reindex(idx_dates).ffill()

            ax_left = ax
            ax_right = ax_left.twinx()

            # Use Plot_setup to plot Adj Close between max/min and shaded and grids)
            ps.plot_price_layer(ax_left)

            #ax_left.plot(idx_dates, bvsp, color="black", label="^BVSP")
            ax_right.plot(ps.plot_index, series, color="blue", label=code)

            ax_left.set_title(f"^BVSP vs {market_info['market']}")
            ax_left.grid(True, linestyle="--", alpha=0.5)

            ps.apply_xaxis(ax_right)
            # Set sparse x-axis ticks
            ax.set_xticks(sparse_positions)
            ax.tick_params(axis="x", labelbottom=False)  # Hide labels (show only on the bottom row)

            h1, l1 = ax_left.get_legend_handles_labels()
            h2, l2 = ax_right.get_legend_handles_labels()
            ax_left.legend(h1 + h2, l1 + l2, loc="upper left")

        for j in range(len(chunk), per_fig):
            axes[j].set_visible(False)



        fig.tight_layout()
        figs.append(fig)

    return figs


