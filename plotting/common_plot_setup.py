from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd
from core.my_data_types import Config, PlotSetup


# ================================================================
# 1. Prepare_plot_data FUNCTION
# ================================================================
def prepare_plot_data(df_idx: pd.DataFrame, df_eod, config: Config) -> PlotSetup:

    # --------------------------------------------------
    # Read values from Config dataclass (NOT dictionary)
    # --------------------------------------------------
    lookback_period = config.graph_lookback

    number_xlabels = 50
    xlabel_separation = max(1, int(lookback_period / number_xlabels))

    # config.market_to_study is still a dict -> OK to iterate
    first_market = next(iter(config.market_to_study.values()))
    idx = first_market["idx_code"]
    mkt = first_market["market"]

    # --------------------------------------------------
    # Count number of tickers in EOD data
    # --------------------------------------------------
    if isinstance(df_eod.columns, pd.MultiIndex):
        num_tickers = df_eod.columns.get_level_values(1).nunique()
    else:
        num_tickers = len(df_eod.columns)

    # --------------------------------------------------
    # Slice the index df for lookback window
    # --------------------------------------------------
    df_slice = df_idx.tail(lookback_period).copy()

    sample_start = df_slice.index.min().strftime('%d/%m/%y')
    sample_end = df_slice.index.max().strftime('%d/%m/%y')

    ymin = df_slice['Adj Close'].min()
    ymax = df_slice['Adj Close'].max()

    # --------------------------------------------------
    # Build x-axis labels (converted to continuous index)
    # --------------------------------------------------
    df_slice_indexed = df_slice.reset_index()
    date_labels = df_slice_indexed['Date'].dt.strftime("%d/%m/%y").tolist()
    slice_to_plot = df_slice_indexed  #.drop(columns=['Date'])

    # --------------------------------------------------
    # Tick spacing
    # --------------------------------------------------
    tick_positions = list(range(0, len(slice_to_plot), xlabel_separation))
    last_pos = len(slice_to_plot) - 1
    if last_pos not in tick_positions:
        if tick_positions and (last_pos - tick_positions[-1] <= 5):
            tick_positions[-1] = last_pos
        else:
            tick_positions.append(last_pos)

    # --------------------------------------------------
    # Return PlotSetup dataclass
    # --------------------------------------------------
    return PlotSetup(
        idx,
        mkt,
        slice_to_plot,
        lookback_period,
        num_tickers,
        sample_start,
        sample_end,
        ymin,
        ymax,
        date_labels,
        tick_positions
    )


# ================================================================
# 2. DEFINE THE HELPER AT MODULE LEVEL (TOP LEVEL)
# ================================================================
def plot_price_background(ax, price_df):
    adj = price_df["Adj Close"]

    ax.plot(
        price_df.index,
        adj,
        color="black",
        linewidth=1.5,
        zorder=4,
    )

    ax.set_ylim(adj.min() * 0.99, adj.max() * 1.01)

    ax.fill_between(
        price_df.index,
        adj,
        color="lightgrey",
        zorder=1,
    )


