
import os
import pandas as pd
import matplotlib.pyplot as plt
from core.constants import yahoo_market_details


def load_index_adj_close(idx_code: str, fileloc) -> pd.Series:
    """
    Load and return the Adjusted Close series for a given index code.

    Args:
        idx_code (str): The index code to load (e.g., "^IXIC").
        fileloc: File locations, including the folder for downloaded Yahoo data.

    Returns:
        pd.Series: The Adjusted Close series, indexed by dates.
    """
    path = os.path.join(fileloc.yahoo_downloaded_data_folder, f"INDEX_{idx_code}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing index file: {path}")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df[~df.index.duplicated(keep="first")]
    if "Adj Close" not in df.columns:
        raise ValueError(f"Adj Close column missing for index {idx_code}")
    return df["Adj Close"].sort_index()


def plot_bvsp_vs_all_indices(ps, fileloc, nrows=3, ncols=2):
    """
    Plot ^BVSP (Ibovespa) versus all other indices in `yahoo_market_details`.

    Args:
        ps: PlotSetup instance, providing BVSP price data and plotting utilities.
        fileloc: File locations, including downloaded Yahoo data folder.
        nrows (int): Number of rows in each figure grid.
        ncols (int): Number of columns in each figure grid.

    Returns:
        list[plt.Figure]: List of generated figures.
    """
    bvsp = ps.price_data["Adj Close"].copy()
    idx_dates = bvsp.index
    figs = []
    per_fig = nrows * ncols

    # Use all `yahoo_market_details` entries except ^BVSP itself
    other_indices = [info for info in yahoo_market_details.values()
                     if info.get("idx_code") not in ("^BVSP", None)]

    # Sparse tick positions and labels
    full_positions = ps.tick_positions if ps.tick_positions else []
    sparse_positions = (
        sorted(set(full_positions[::5] + [full_positions[-1]]))
        if full_positions else []
    )
    xlabels = [ps.date_labels[j] for j in sparse_positions] if ps.date_labels else []

    # Plot each chunk of indices
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
            market = market_info['market']
            try:
                # Load and align index series
                series = load_index_adj_close(code, fileloc)
                series = series.reindex(idx_dates).ffill()

                # Create dual y-axis plot
                ax_left = ax
                ax_right = ax_left.twinx()

                # Plot BVSP on the left y-axis
                ps.plot_price_layer(ax_left)
                ax_left.set_ylabel(f"IBOV R$", fontsize=8)

                # Plot the other index on the right y-axis
                ax_right.plot(ps.plot_index, series, color="blue", label=code, linewidth=1.2)

                # Set grid, title, and legends
                ax_left.set_title(f"BVSP vs " + r"$\mathbf{" + market + "}$", fontsize=12)

                ax_left.grid(True, linestyle="--", alpha=0.5)

                # Handle legends
                h1, l1 = ax_left.get_legend_handles_labels()
                h2, l2 = ax_right.get_legend_handles_labels()
                ax_left.legend(h1 + h2, l1 + l2, loc="upper left")

                # Set sparse x-axis ticks
                ax.set_xticks(sparse_positions)
                ax.tick_params(axis="x", labelbottom=False)

            except Exception as e:
                ax.text(0.5, 0.5, f"Error loading {code}: {e}",
                        ha="center", va="center")
                ax.set_visible(True)

        # Show labels only on the bottom row
        for i, ax in enumerate(axes):
            if i // ncols == nrows - 1 and i < len(chunk):
                ax.set_xticklabels(xlabels, rotation=45, fontsize=8)
                ax.tick_params(axis="x", labelbottom=True)

        # Hide unused axes
        for j in range(len(chunk), per_fig):
            axes[j].axis("off")

        # Finalize figure layout
        fig.tight_layout()
        figs.append(fig)

    return figs