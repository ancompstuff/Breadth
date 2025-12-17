import os
import matplotlib.pyplot as plt
import pandas as pd

from core.my_data_types import PlotSetup
from core.constants import yahoo_market_details

def _load_index_series(fileloc, idx_code):
    """
    Load a single Yahoo INDEX csv by code (e.g., '^BVSP', '^IXIC').
    Returns a DataFrame with a Date index and at least 'Adj Close' (or 'Close' fallback).
    """
    path = os.path.join(fileloc.yahoo_downloaded_data_folder, f"INDEX_{idx_code}.csv")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.duplicated(keep="first")].sort_index()

    # Ensure Adj Close is present
    if "Adj Close" not in df.columns:
        if "Close" in df.columns:
            df["Adj Close"] = df["Close"]
        else:
            # Pick first numeric column as fallback
            num = df.select_dtypes(include="number").columns
            if len(num) > 0:
                df["Adj Close"] = df[num[0]]
            else:
                raise ValueError(f"INDEX_{idx_code}.csv missing 'Adj Close'/'Close' or any numeric column.")
    return df


def _align_series_to_ps_index(series: pd.Series, target_index: pd.Index) -> pd.Series:
    """
    Align a daily series to PlotSetup price index:
      - reindex to target_index
      - forward-fill
      - if NaNs remain (rare due to calendar mismatches), merge_asof fallback

    Robust against missing/None series.name by building 'right' explicitly.
    """
    s = series.sort_index().reindex(target_index).ffill()
    if s.isna().any():
        # Build left/right with explicit 't'/'val' columns to avoid KeyError
        left = pd.DataFrame({"t": pd.Index(target_index)})
        right = pd.DataFrame({"t": series.index, "val": series.values})
        merged = pd.merge_asof(
            left.sort_values("t"),
            right.sort_values("t"),
            on="t",
            direction="backward"
        )
        # FIX: use keyword argument 'name=' (previously had a function call 'name(...)')
        s = pd.Series(merged["val"].values, index=target_index, name=(series.name if series.name else "Adj Close")).ffill()
    return s


def plot_bvsp_vs_all_indices(ps: PlotSetup, fileloc, nrows: int = 3, ncols: int = 2):
    """
    Plot ^BVSP vs a grid of other major indexes.
    Matches plot_bcb_grid style:
      - sharex=False
      - explicit sparse xticks
      - labels only on the bottom-most used row
      - fixed x-limits via PlotSetup (ps.fix_xlimits + margins)
      - twin y-axis with right-axis label for each compared index
    Returns a list of Figures.
    """
    # Build list of other index codes from yahoo_market_details (exclude the one being studied)
    idx_bvsp = ps.idx
    other_idx_codes = []
    code_to_market = {}  # <--- Create this helper dictionary
    for _, info in yahoo_market_details.items():
        code = info.get("idx_code")
        market = info.get("market")
        if code and code != idx_bvsp:
            other_idx_codes.append(code)
            # Store the market name using the code as the key
            code_to_market[code] = market

    # Align BVSP Adj Close to PlotSetup index
    df_bvsp = _load_index_series(fileloc, idx_bvsp)
    adj_bvsp = _align_series_to_ps_index(df_bvsp["Adj Close"], ps.price_data.index).values

    # Left axis limits from BVSP only
    left_min = pd.Series(adj_bvsp).min()
    left_max = pd.Series(adj_bvsp).max()

    # Sparse tick positions and labels
    full_positions = ps.tick_positions
    step_size = 5
    if not full_positions:
        sparse_positions = []
        xlabels = []
    else:
        # 1. Generate the sparse positions by stepping backward (reverse list)
        # We use list(reversed(...)) or full_positions[::-1] to step backward.
        # Then, we slice [::step_size] to get every 5th element.
        sparse_backwards = full_positions[::-1][::step_size]

        # 2. Reverse the list back to chronological order
        # Since we started from the end, we must reverse it back to chronological order for plotting.
        sparse_positions = sorted(sparse_backwards)

        # 3. Ensure the very first tick is included (optional, but good practice)
        if full_positions[0] not in sparse_positions:
            sparse_positions.insert(0, full_positions[0])
        #sparse_positions = sorted(set(full_positions[::5] + [full_positions[-1]]))

        xlabels = [ps.date_labels[j] for j in sparse_positions]

    x = ps.plot_index
    figs: list[plt.Figure] = []
    per_fig = nrows * ncols
    total_series = len(other_idx_codes)

    # Loop over pages
    for start in range(0, total_series, per_fig):
        end = min(start + per_fig, total_series)
        chunk = other_idx_codes[start:end]

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=(18, 9),
            sharex=False,
            #constrained_layout=True,
        )
        figs.append(fig)
        axes = axes.flatten()

        # Identify last used row for this page
        last_used_index = len(chunk) - 1
        last_used_row = last_used_index // ncols
        bottom_row_axes = []

        for i, idx_code in enumerate(chunk):

            # Look up the market name for the current idx_code
            # .get() is safer in case a code is missing
            current_market = code_to_market.get(idx_code, "Unknown Market")

            ax_left = axes[i]

            # Left axis: BVSP
            ax_left.plot(x, adj_bvsp, color="black", linewidth=1.3, label=idx_bvsp)
            ax_left.fill_between(x, adj_bvsp, color="lightgrey", alpha=0.4)
            ax_left.set_ylim(left_min, left_max)
            ax_left.set_ylabel("Adj Close", fontsize=8)
            ax_left.tick_params(axis="y", labelsize=8)
            ax_left.grid(True, axis="x", linestyle="-", alpha=0.3, color="gray", linewidth=0.8)

            # Right axis: other index (own scale)
            df_other = _load_index_series(fileloc, idx_code)
            other_adj = _align_series_to_ps_index(df_other["Adj Close"], ps.price_data.index)
            ax_right = ax_left.twinx()
            ax_right.plot(
                x,
                other_adj.values,
                linewidth=1.2,
                color="tab:blue",
                label=idx_code,
            )
            ax_right.set_ylabel(idx_code, fontsize=8)  # twin y-axis label
            ax_right.tick_params(axis="y", labelsize=8)

            # Explicit xticks everywhere
            ax_left.set_xticks(sparse_positions)
            # Hide labels for all but bottom row; we set them later
            ax_left.tick_params(axis="x", labelbottom=False)

            # Title
            ax_left.set_title(f"{idx_bvsp} vs {current_market} ({idx_code})", fontsize=10)

            # Legend (combine both axes)
            h_left, l_left = ax_left.get_legend_handles_labels()
            h_right, l_right = ax_right.get_legend_handles_labels()
            ax_left.legend(h_left + h_right, l_left + l_right, loc="upper left", fontsize=7)

            # Match BVSP vs BCB width handling
            ps.fix_xlimits(ax_left)           # enforce full PlotSetup window
            ax_left.margins(x=0)              # no extra x padding
            ax_right.set_xlim(ax_left.get_xlim())  # sync twin x-limits

            # Track bottom-most used row axes
            if (i // ncols) == last_used_row:
                bottom_row_axes.append(ax_left)

        # Hide unused axes on this page
        for j in range(len(chunk), per_fig):
            axes[j].set_visible(False)

        # Show x labels only on bottom-most used row
        for ax in bottom_row_axes:
            ax.tick_params(axis="x", labelbottom=True)
            ax.set_xticklabels(xlabels, rotation=45, fontsize=8)

    return figs