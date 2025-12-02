import os
import pandas as pd
import matplotlib.pyplot as plt

from indicators.indicator_bcb import selic_vs_index_df, ipca_vs_index_df


def plot_idx1_v_idx2(idx1, idx2, config, fileloc, ps):
    """
    idx1: primary index (must match ps.idx)
    idx2: secondary index (e.g., 'BRL=X')
    IBOV comes from PlotSetup.price_data.
    idx2 and BCB series are loaded from CSV files.
    """

    lookback = int(getattr(config, "graph_lookback", 252))
    csv_folder = fileloc.downloaded_data_folder

    # ---------------------------------------------------------
    # 1) IBOV = ps.price_data (already aligned and trimmed)
    # ---------------------------------------------------------
    ibov_df = ps.price_data.tail(lookback).copy()
    x = ps.plot_index[-len(ibov_df):]  # numeric x-axis

    # Detect price column
    if "Adj Close" in ibov_df.columns:
        ibov_col = "Adj Close"
    elif "Close" in ibov_df.columns:
        ibov_col = "Close"
    else:
        ibov_col = ibov_df.select_dtypes("number").columns[0]

    ibov_price = ibov_df[ibov_col].values

    # ---------------------------------------------------------
    # 2) Load idx2 (secondary index) directly from CSV
    # ---------------------------------------------------------
    idx2_path = os.path.join(csv_folder, f"INDEX_{idx2}.csv")
    if not os.path.exists(idx2_path):
        raise RuntimeError(f"Cannot find file {idx2_path}")

    df_idx2 = pd.read_csv(idx2_path, index_col=0, parse_dates=True)
    df_idx2 = df_idx2.loc[ibov_df.index].copy()  # align to IBOV datetime

    # detect idx2 price column
    if "Adj Close" in df_idx2.columns:
        idx2_col = "Adj Close"
    elif "Close" in df_idx2.columns:
        idx2_col = "Close"
    else:
        idx2_col = df_idx2.select_dtypes("number").columns[0]

    idx2_price = df_idx2[idx2_col].values

    # ---------------------------------------------------------
    # 3) Rolling correlation between IBOV and idx2
    # ---------------------------------------------------------
    corr_df = pd.DataFrame({
        "IBOV": ibov_price,
        "IDX2": idx2_price,
    })

    corr_df["Corr"] = corr_df.IBOV.rolling(20).corr(corr_df.IDX2)

    # ---------------------------------------------------------
    # 4) Load BCB monthly data (SELIC + IPCA)
    # ---------------------------------------------------------
    bcb_path = os.path.join(csv_folder, "bcb", "BCB_IPCA_SELIC.csv")
    if not os.path.exists(bcb_path):
        raise RuntimeError(f"Missing BCB file: {bcb_path}")

    df_bcb = pd.read_csv(bcb_path, index_col=0, parse_dates=True)

    # Forward-fill SELIC/IPCA to IBOV dates
    df_selic = selic_vs_index_df(df_bcb, ibov_df)
    df_ipca = ipca_vs_index_df(df_bcb, ibov_df)

    # ---------------------------------------------------------
    # 5) Prepare figure
    # ---------------------------------------------------------
    fig, (ax_corr, ax_selic, ax_ipca) = plt.subplots(3, 1, figsize=(18, 14), sharex=True)

    # ---------------------------------------------------------
    # Helper: IBOV shaded layer
    # ---------------------------------------------------------
    def draw_ibov(ax):
        ps.plot_price_layer(ax)  # uses numeric index + grey shading
        ax.set_ylabel("^BVSP", color="black")

    # =========================================================
    # Subplot 1 — IBOV vs idx2 + correlation
    # =========================================================
    draw_ibov(ax_corr)

    # idx2 line
    ax_r = ax_corr.twinx()
    ax_r.plot(x, idx2_price, color="green", linewidth=1.2)
    ax_r.set_ylabel(idx2, color="green")

    # correlation (3rd axis)
    ax_c = ax_corr.twinx()
    ax_c.spines["right"].set_position(("outward", 60))
    ax_c.plot(x, corr_df["Corr"], color="blue", linewidth=1.4)
    ax_c.axhline(0, color="blue", linestyle=":")
    ax_c.set_ylim(-1.05, 1.05)

    ax_corr.set_title(f"{idx1} vs {idx2} (20-day correlation)")

    # =========================================================
    # Subplot 2 — SELIC vs IBOV
    # =========================================================
    draw_ibov(ax_selic)

    ax_s_r = ax_selic.twinx()
    ax_s_r.plot(x, df_selic["SELIC"].values, linewidth=1.1)
    ax_s_r.set_ylabel("SELIC", color="tab:blue")

    ax_selic.set_title("SELIC vs ^BVSP")

    # =========================================================
    # Subplot 3 — IPCA vs IBOV
    # =========================================================
    draw_ibov(ax_ipca)

    ax_i_r = ax_ipca.twinx()
    ax_i_r.plot(x, df_ipca["IPCA"].values, linewidth=1.1, color="tab:orange")
    ax_i_r.set_ylabel("IPCA", color="tab:orange")

    ax_ipca.set_title("IPCA vs ^BVSP")

    # ---------------------------------------------------------
    # Final shared x-axis (tick labels only on bottom subplot)
    # ---------------------------------------------------------
    ps.apply_xaxis(ax_ipca)

    fig.tight_layout()
    return fig
