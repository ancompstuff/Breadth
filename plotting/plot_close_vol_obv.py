import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.my_data_types import PlotSetup

def plot_close_vol_obv(ps: PlotSetup, df_in: pd.DataFrame):
    """
    Plot price, volume, OBV and cumulative NMF + component aggregates.
    df must already contain:
        Volume, OBV, NMF_cum, Bearish, Bullish,
        Comp_OBV_norm_mean, Comp_NMF_norm_mean,
        Comp_Bearish, Comp_Bullish (optional, if you want component shading)
    """
    df_indicators = df_in.loc[ps.price_data.index].copy()

    fig, (axtop, axbot, axheat) = plt.subplots(
        3, 1, figsize=(18, 9),
        sharex=True,
        height_ratios=[5, 5, 1]
    )

    # =============================================
    # TOP — PRICE + VOLUME bars (unchanged)
    # =============================================
    axtop.set_title(
        f"{ps.mkt} — Preço/Volume ({ps.sample_start} - {ps.sample_end})",
        fontsize=12, fontweight="bold"
    )
    ps.plot_price_layer(axtop)

    ax2 = axtop.twinx()
    colors = np.where(ps.price_data["Adj Close"].diff().fillna(0) >= 0, "green", "red")
    ax2.bar(ps.plot_index, df_indicators["Volume"] / 1000, color=colors, width=0.8,
            zorder=3, alpha=0.5, label="Volume")
    ax2.grid(True, axis='y', linestyle='-', alpha=0.3, color='gray', linewidth=0.8)
    ax2.set_ylabel('Volume', color='black')

    # =============================================
    # MID — PRICE + OBV + NMF (INDEX + COMPONENT AGG)
    # =============================================
    axbot.set_title(f"{ps.mkt} — OBV & Net Money Flow", fontsize=12)
    ps.plot_price_layer(axbot)

    # Index shading (unchanged)
    axbot.fill_between(ps.plot_index, df_indicators["Adj Close"],
                       where=df_indicators["Bearish"] == 1, color="red", alpha=0.2)
    axbot.fill_between(ps.plot_index, df_indicators["Adj Close"],
                       where=df_indicators["Bullish"] == 1, color="green", alpha=0.2)

    # Use normalized series produced by indicator function if present,
    # otherwise fall back to local normalization.
    if "OBV_norm" in df_indicators.columns and "NMF_norm" in df_indicators.columns:
        obv_norm = df_indicators["OBV_norm"]
        nmf_norm = df_indicators["NMF_norm"]
    else:
        obv_norm = (df_indicators["OBV"] - df_indicators["OBV"].min()) / (df_indicators["OBV"].max() - df_indicators["OBV"].min())
        nmf_norm = (df_indicators["NMF_cum"] - df_indicators["NMF_cum"].min()) / (df_indicators["NMF_cum"].max() - df_indicators["NMF_cum"].min())

    ax3 = axbot.twinx()

    # Index lines
    ax3.plot(ps.plot_index, obv_norm, label="Index OBV (norm)", linewidth=1.5)
    ax3.plot(ps.plot_index, nmf_norm, label="Index NMF (norm)", linewidth=1.5)

    # Component aggregate lines (NEW)
    if "Comp_OBV_norm_mean" in df_indicators.columns:
        ax3.plot(ps.plot_index, df_indicators["Comp_OBV_norm_mean"],
                 label="Components OBV (mean norm)", linewidth=1.2, linestyle="--")
    if "Comp_NMF_norm_mean" in df_indicators.columns:
        ax3.plot(ps.plot_index, df_indicators["Comp_NMF_norm_mean"],
                 label="Components NMF (mean norm)", linewidth=1.2, linestyle="--")

    ax3.set_ylabel('OBV / NMF (normalizado)', color='black')
    ax3.legend(loc="upper left")
    ax3.grid(True, axis='y', linestyle='-', alpha=0.3, color='gray', linewidth=0.8)

    # =============================================
    # HEATMAP — volume / obv / nmf (+ components)
    # =============================================
    vol_norm = ((df_indicators["Volume"] - df_indicators["Volume"].min()) /
                (df_indicators["Volume"].max() - df_indicators["Volume"].min()))

    # these should already be 0..1 (from compute_close_vol_obv)
    comp_obv = df_indicators["Comp_OBV_norm_mean"]
    comp_nmf = df_indicators["Comp_NMF_norm_mean"]

    heat = np.vstack([
        vol_norm.values,
        obv_norm.values,
        nmf_norm.values,
        comp_obv.values,
        comp_nmf.values,
    ])

    axheat.imshow(heat, aspect="auto", cmap="hot", vmin=0, vmax=1)
    axheat.set_yticks([0, 1, 2, 3, 4])
    axheat.set_yticklabels(
        ["Volume", "Index OBV", "Index NMF", "Comp OBV", "Comp NMF"],
        fontsize=8
    )