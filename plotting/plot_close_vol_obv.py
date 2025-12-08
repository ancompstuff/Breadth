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
    # Align indicators dataframe to the same datetime index as ps
    df_indicators = df_in.loc[ps.price_data.index].copy()

    # ---------------------------------------------
    fig, (axtop, axbot, axheat) = plt.subplots(
        3, 1, figsize=(18, 9),
        sharex=True,
        height_ratios=[5, 5, 1]
    )
    # =============================================
    # TOP — PRICE + VOLUME bars
    # =============================================
    axtop.set_title(f"{ps.mkt} — Preço/Volume ({ps.sample_start} - {ps.sample_end})", fontsize=12, fontweight="bold")

    # Use Plot_setup to plot Adj Close between max/min and shaded and grids)
    ps.plot_price_layer(axtop)

    # Volume colored by price direction
    ax2 = axtop.twinx()
    colors = np.where(ps.price_data["Adj Close"].diff().fillna(0) >= 0, "green", "red")
    ax2.bar(ps.plot_index, df_indicators["Volume"]/1000, color=colors, width=0.8, zorder=3, alpha=0.5, label="Volume")
    ax2.grid(True, axis='y', linestyle='-', alpha=0.3, color='gray', linewidth=0.8)
    ax2.set_ylabel('Volume', color='black')

    # =============================================
    # MID — PRICE + OBV + NMF
    # =============================================
    axbot.set_title(f"{ps.mkt} — OBV & Net Money Flow", fontsize=12)

    # Use Plot_setup to plot Adj Close between max/min and shaded and grids)
    ps.plot_price_layer(axbot)

    # Shading
    axbot.fill_between(ps.plot_index, df_indicators["Adj Close"], where=df_indicators["Bearish"]==1, color="red", alpha=0.2)
    axbot.fill_between(ps.plot_index, df_indicators["Adj Close"], where=df_indicators["Bullish"]==1, color="green", alpha=0.2)

    # OBV/NMF normalized for overlay
    obv_norm = (df_indicators["OBV"] - df_indicators["OBV"].min()) / (df_indicators["OBV"].max() - df_indicators["OBV"].min())
    nmf_norm = (df_indicators["NMF_cum"] - df_indicators["NMF_cum"].min()) / (df_indicators["NMF_cum"].max() - df_indicators["NMF_cum"].min())

    ax3 = axbot.twinx()
    ax3.plot(ps.plot_index, obv_norm, label="OBV (normalizado)")
    ax3.plot(ps.plot_index, nmf_norm, label="NMF_cum (normalizado)")
    ax3.set_ylabel('OBV / NMF cumulativo', color='black')
    ax3.legend(loc="upper left")
    ax3.grid(True, axis='y', linestyle='-', alpha=0.3, color='gray', linewidth=0.8)


    # =============================================
    # HEATMAP — volume / obv / nmf
    # =============================================
    vol_norm = ((df_indicators["Volume"] - df_indicators["Volume"].min()) /
                (df_indicators["Volume"].max() - df_indicators["Volume"].min()))

    heat = np.vstack([
        vol_norm.values,
        obv_norm.values,
        nmf_norm.values
    ])
    axheat.imshow(heat, aspect="auto", cmap="hot")
    axheat.set_yticks([0,1,2])
    axheat.set_yticklabels(["Volume", "OBV", "NMF"], fontsize=8)

    # X-axis formatting via PlotSetup
    ps.apply_xaxis(axheat)

    return fig
