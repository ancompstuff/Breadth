import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.my_data_types import PlotSetup

def plot_close_vol_obv(ps: PlotSetup, df_in: pd.DataFrame):
    """
    Plot price, volume, OBV and cumulative NMF.
    df must already contain:
        OBV, NMF_cum, Bearish, Bullish
    ps.df_to_plot is already sliced to the correct lookback.
    """

    dates_to_plot = ps.slice_to_plot['Date'].values
    df_indicators = df_in.loc[dates_to_plot].reset_index(drop=True)
    # df_indicators.index is now the same as ps.to_plot_slice.index

    left_yaxis_data = ps.slice_to_plot.copy()
    date_labels = ps.date_labels
    tick_positions = ps.tick_positions

    # ---------------------------------------------
    fig, (axtop, axbot, ax_heat) = plt.subplots(
        3, 1, figsize=(18, 9),
        sharex=True,
        height_ratios=[5, 5, 1]
    )

    # =============================================
    # TOP — PRICE + VOLUME bars
    # =============================================
    axtop.set_title(f"{ps.mkt} — Preço/Volume ({ps.sample_start} - {ps.sample_end})", fontsize=12, fontweight="bold")

    ps.plot_price_background(axtop, left_yaxis_data)

    # Price
    axtop.plot(left_yaxis_data.index, left_yaxis_data["Adj Close"], color="black", linewidth=1.5, zorder=4)
    axtop.set_ylim(left_yaxis_data['Adj Close'].min() * 0.99, left_yaxis_data['Adj Close'].max() * 1.01)  # Add 1% padding
    axtop.fill_between(left_yaxis_data.index, left_yaxis_data["Adj Close"], color="lightgrey")

    # Volume colored by price direction
    colors = np.where(left_yaxis_data["Adj Close"].diff().fillna(0) >= 0, "green", "red")
    ax2 = axtop.twinx()
    ax2.bar(df_indicators.index, df_indicators["Volume"]/1000, color=colors, width=0.8, zorder=3)

    # =============================================
    # MID — PRICE + OBV + NMF
    # =============================================
    axbot.set_title(f"{ps.mkt} — OBV & Net Money Flow", fontsize=12)

    # Price for reference
    ps.plot_price_background(axbot, left_yaxis_data)


    # Shading
    axbot.fill_between(left_yaxis_data.index, left_yaxis_data["Adj Close"], where=left_yaxis_data["Bearish"]==1, color="red", alpha=0.2)
    axbot.fill_between(left_yaxis_data.index, left_yaxis_data["Adj Close"], where=left_yaxis_data["Bullish"]==1, color="green", alpha=0.2)

    # OBV/NMF normalized for overlay
    obv_norm = (df_indicators["OBV"] - df_indicators["OBV"].min()) / (df_indicators["OBV"].max() - df_indicators["OBV"].min())
    nmf_norm = (df_indicators["NMF_cum"] - df_indicators["NMF_cum"].min()) / (df_indicators["NMF_cum"].max() - df_indicators["NMF_cum"].min())

    ax3 = axbot.twinx()
    ax3.plot(df_indicators.index, obv_norm, label="OBV (normalizado)")
    ax3.plot(df_indicators.index, nmf_norm, label="NMF_cum (normalizado)")

    ax3.legend(loc="upper left")

    # =============================================
    # HEATMAP — volume / obv / nmf
    # =============================================
    vol_norm = (df_indicators["Volume"] - df_indicators["Volume"].min()) / (df_indicators["Volume"].max() - df_indicators["Volume"].min())

    heat = np.vstack([
        vol_norm.values,
        obv_norm.values,
        nmf_norm.values
    ])

    ax_heat.imshow(heat, aspect="auto", cmap="hot")
    ax_heat.set_yticks([0,1,2])
    ax_heat.set_yticklabels(["Volume", "OBV", "NMF"], fontsize=8)

    # X-axis formatting via PlotSetup
    ps.apply_xaxis(ax_heat)

    return fig
