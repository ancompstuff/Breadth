# ---------------------------------------
# Standard library
# ---------------------------------------
import os
import time
from datetime import datetime
from dataclasses import replace

# ---------------------------------------
# Third-party
# ---------------------------------------
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---------------------------------------
# Project / internal imports
# ---------------------------------------
from core.constants import file_locations
from core.my_data_types import load_file_locations_dict
from main_modules.user_setup import what_do_you_want_to_do
from main_modules.update_or_create import update_or_create_databases
from utils.align_dataframes import align_and_prepare_for_plot


def debug_ftse_density(idx_ma_df: pd.DataFrame, comp_ma_df: pd.DataFrame):
    """
    Prints a diagnostic report on data availability for the FTSE350.
    """
    print("=== FTSE350 DATA DENSITY DEBUG ===")

    # 1. Check Index Coverage
    total_dates = len(idx_ma_df.index)
    print(f"Total dates in index: {total_dates}")

    # 2. Check VWMA Column Presence
    vwma_cols = comp_ma_df.columns.get_level_values(0).unique()
    print(f"VWMA Columns found: {list(vwma_cols)}")

    # 3. Analyze Density per VWMA Period
    for col_prefix in vwma_cols:
        if col_prefix.startswith("C-VWMA"):
            sub_df = comp_ma_df[col_prefix]
            # Calculate what % of the dataframe is actually populated (not NaN)
            density = sub_df.notna().sum().sum() / sub_df.size

            # Check for the "Spike" at the end (Last 5 days vs First 5 days)
            recent_density = sub_df.tail(5).notna().mean().mean()
            early_density = sub_df.head(5).notna().mean().mean()

            print(f"\nIndicator: {col_prefix}")
            print(f" -> Overall Fill Rate: {density:.2%}")
            print(f" -> Start of sample Fill Rate: {early_density:.2%}")
            print(f" -> End of sample Fill Rate: {recent_density:.2%}")
            print(f" -> Active tickers at end: {sub_df.iloc[-1].notna().sum()} / {len(sub_df.columns)}")

    # 4. Check for Zero-Width ranges (The 'Black' Heatmap Cause)
    # The heatmap uses (max - min). If all tickers have the SAME value (e.g., 0 or NaN),
    # the width is 0, resulting in a black plot.
    for col_prefix in vwma_cols:
        if col_prefix.startswith("C-VWMA"):
            width = comp_ma_df[col_prefix].max(axis=1) - comp_ma_df[col_prefix].min(axis=1)
            zeros = (width == 0).sum()
            print(f" -> Dates with Zero Dispersion (Width=0): {zeros} days")


# ---------------------------
# 1. Load + align market data
# ---------------------------

def load_and_align_data(fileloc):
    # 1) Main user choice
    config = what_do_you_want_to_do(fileloc)

    # 2) Ask BCB update IMMEDIATELY after
    from main_modules.update_bcb_y_or_n import ask_update_bcb
    update_bcb = ask_update_bcb()

    # 3) Build / update market databases
    index_df, components_df = update_or_create_databases(config, fileloc)

    # 4) Align calendars
    index_df, components_df = align_and_prepare_for_plot(
        index_df, components_df
    )

    return config, update_bcb, index_df, components_df


# -------------------------------
# 2. Load BCB + USD macro data
# -------------------------------
def load_macro_data(fileloc, trading_index, update_bcb):
    if update_bcb:
        from main_modules.build_bcb_files import build_bcb_files
        build_bcb_files(fileloc)

    # Load BCB ready file
    trading_path = os.path.join(
        fileloc.bacen_downloaded_data_folder,
        "bcb_dashboard_ready_trading.csv",
    )
    calendar_path = os.path.join(
        fileloc.bacen_downloaded_data_folder,
        "bcb_dashboard_ready.csv",
    )

    if os.path.exists(trading_path):
        df_bcb = pd.read_csv(trading_path, index_col="date", parse_dates=True)
    else:
        df_bcb = pd.read_csv(calendar_path, index_col="date", parse_dates=True)

    df_bcb_daily = df_bcb.reindex(trading_index).ffill()

    # Load USD
    from utils.load_usd_from_files import load_usd_series
    usd_raw = load_usd_series(fileloc)
    usd_series = usd_raw.reindex(trading_index).ffill()

    return df_bcb_daily, usd_series


# ---------------------------------------
# 3. Compute all indicators (NO plotting)
# ---------------------------------------
def compute_indicators(index_df, components_df, ps):
    from indicators.close_vol_obv import compute_close_vol_obv
    import indicators.hi_lo_indicators as ihi
    from core.constants import ma_groups
    import indicators.ma_indicators_1 as mai
    import indicators.ma_indicators_2 as mai2
    import indicators.adv_dec_indicators as adi

    out_close_vol = compute_close_vol_obv(index_df, components_df)

    hi_lo_diff = ihi.calculate_highs_and_lows(components_df)

    df_idx_mas, df_eod_mas = mai.calculate_idx_and_comp_ma_vwma(
        index_df, components_df
    )
    df_idx_with_osc = mai.calc_conver_diver_oscillator(df_idx_mas, ps)

    df_idx_agg = mai.calculate_tickers_over_under_mas(
        df_idx_mas, df_eod_mas, ps
    )

    adv_dec_indicators = adi.calculate_advance_decline(index_df, components_df)

    df_idx_compress, df_comp_compress = mai.calculate_compressao_dispersao(
        df_idx_mas, df_eod_mas
    )

    ladder, mini_ladders = mai2.build_vwma_ladders(df_eod_mas, index_df)

    return {
        "close_vol": out_close_vol,
        "hi_lo_diff": hi_lo_diff,
        "adv_dec_indicators": adv_dec_indicators,
        "idx_with_osc": df_idx_with_osc,
        "idx_agg": df_idx_agg,
        "idx_compress": df_idx_compress,
        "comp_compress": df_comp_compress,
        "ladder": ladder,
        "mini_ladders": mini_ladders,
    }  #  this is a dictionary, currently with no name. Named in main.py


# ---------------------------------------
# 4. Build all figures (NO calculations)
# ---------------------------------------
def build_figures(ps, ps_long, indicators, df_bcb_daily, usd_series, fileloc):
    from plotting.plot_close_vol_obv import plot_close_vol_obv
    import plotting.plot_hi_lo as phi
    import plotting.plot_ma_indicators_1 as pmai
    import plotting.plot_ma_indicators_2 as pmai2
    import plotting.plot_adv_dec as pad
    from plotting.plot_bcb_grid import plot_bcb_grid
    import plotting.plot_bvsp_vs_indexes as ppbi

    figs = []

    figs.append(
        plot_close_vol_obv(ps, indicators["close_vol"])
    )

    figs.append(
        phi.plot_highs_and_lows(ps, indicators["hi_lo_diff"])
    )

    figs.append(
        pad.plot_breadth_breakout(indicators["adv_dec_indicators"], ps)
    )

    figs.append(
        pmai.plot_index_vs_ma_vwma(indicators["idx_with_osc"], ps)
    )

    figs.append(
        pmai.plot_tickers_over_under_mas(indicators["idx_agg"], ps)
    )

    figs.append(
        pmai.plot_absolute_compression_bands(
            indicators["idx_compress"],
            indicators["comp_compress"],
            ps,
        )
    )

    figs.append(
        pmai2.plot_vwma_percent_trends_4panels(
            ps,
            indicators["ladder"],
            indicators["mini_ladders"],  # for panels 1-3
        )
    )

    figs.extend(
        plot_bcb_grid(
            ps_long,
            df_bcb_daily,
            usd_series=usd_series,
            nrows=3,
            ncols=2,
        )
    )

    figs.extend(
        ppbi.plot_bvsp_vs_all_indices(ps_long, fileloc, nrows=3, ncols=2)
    )


    return figs


# ---------------------------------------
# 5. Export PDF + open
# ---------------------------------------
def export_pdf_and_open(figs, fileloc, ps):
    pdf_name = f"{ps.mkt} breadth_{datetime.today().strftime('%Y-%m-%d')}.pdf"
    pdf_path = os.path.join(fileloc.pdf_folder, pdf_name)

    with PdfPages(pdf_path) as pdf:
        for fig in figs:
            pdf.savefig(fig)
            plt.close(fig)

    time.sleep(0.5)

    if os.path.exists(pdf_path):
        try:
            os.startfile(pdf_path)
        except Exception:
            pass


###############################################################
# ------------------------  MAIN  -----------------------------
###############################################################
def main():
    from core.my_data_types import timed_block

    with timed_block("Load file locations"):
        fileloc = load_file_locations_dict(file_locations)

    with timed_block("Load + align market data"):
        config, update_bcb, index_df, components_df = load_and_align_data(fileloc)

        # --- CODE TO SAVE DATAFRAMES ---
        # Ensure the data directory exists in your repo
        data_dir = "data_cache"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Save to parquet for high-speed testing
        index_df.to_parquet(os.path.join(data_dir, "index_df.parquet"))
        components_df.to_parquet(os.path.join(data_dir, "components_df.parquet"))
        print(f"DataFrames cached successfully in {data_dir}/")
        # -----------------------------------

    with timed_block("Prepare PlotSetup"):
        from plotting.common_plot_setup import prepare_plot_data
        ps = prepare_plot_data(index_df, components_df, config)
        ps_long = prepare_plot_data(
            index_df,
            components_df,
            replace(config, graph_lookback=config.graph_lookback * 5),
        )

    with timed_block("Load BCB + USD macro data"):
        df_bcb_daily, usd_series = load_macro_data(
            fileloc,
            ps_long.price_data.index,
            update_bcb,
        )

    with timed_block("Compute indicators"):
        indicators = compute_indicators(index_df, components_df, ps)

    with timed_block("Build figures"):
        figs = build_figures(
            ps,
            ps_long,
            indicators,
            df_bcb_daily,
            usd_series,
            fileloc,
        )

    with timed_block("Export PDF + open"):
        export_pdf_and_open(figs, fileloc, ps)


if __name__ == "__main__":
    main()
