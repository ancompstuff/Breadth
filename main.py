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

# --- Indicator & Summary Imports ---
from indicators.swing_metrics import compute_swing_metrics
from signals.swing_summary import print_and_plot_summary_page

# Plotting module imports
from plotting.plot_close_vol_obv import plot_close_vol_obv
import plotting.plot_hi_lo as phi
from plotting.plot_breakout_indicators import plot_breakouts
import plotting.plot_ma_indicators_2 as pmai2
import plotting.plot_adv_dec as pad
from plotting.plot_ttm_volatility import plot_aggregate_ttm_squeeze


def debug_ftse_density(idx_ma_df: pd.DataFrame, comp_ma_df: pd.DataFrame):
    """
    Prints a diagnostic report on data availability for the FTSE350.
    """
    print("=== FTSE350 DATA DENSITY DEBUG ===")

    total_dates = len(idx_ma_df.index)
    print(f"Total dates in index: {total_dates}")

    vwma_cols = comp_ma_df.columns.get_level_values(0).unique()
    print(f"VWMA Columns found: {list(vwma_cols)}")

    for col_prefix in vwma_cols:
        if col_prefix.startswith("C-VWMA"):
            sub_df = comp_ma_df[col_prefix]
            density = sub_df.notna().sum().sum() / sub_df.size
            recent_density = sub_df.tail(5).notna().mean().mean()
            early_density = sub_df.head(5).notna().mean().mean()

            print(f"\nIndicator: {col_prefix}")
            print(f" -> Overall Fill Rate: {density:.2%}")
            print(f" -> Start of sample Fill Rate: {early_density:.2%}")
            print(f" -> End of sample Fill Rate: {recent_density:.2%}")
            print(f" -> Active tickers at end: {sub_df.iloc[-1].notna().sum()} / {len(sub_df.columns)}")

    for col_prefix in vwma_cols:
        if col_prefix.startswith("C-VWMA"):
            width = comp_ma_df[col_prefix].max(axis=1) - comp_ma_df[col_prefix].min(axis=1)
            zeros = (width == 0).sum()
            print(f" -> Dates with Zero Dispersion (Width=0): {zeros} days")


# ---------------------------
# 1. Load + align market data
# ---------------------------
def load_and_align_data(fileloc):
    config = what_do_you_want_to_do(fileloc)

    from main_modules.update_bcb_y_or_n import ask_update_bcb
    update_bcb = ask_update_bcb()

    index_df, components_df = update_or_create_databases(config, fileloc)

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
    from indicators.breakout_indicators import add_breakout_columns
    from indicators.ttm_volatility import compute_aggregate_ttm_squeeze

    out_close_vol = compute_close_vol_obv(index_df, components_df)
    hi_lo_diff = ihi.calculate_highs_and_lows(components_df)

    df_idx_breakouts, df_eod_breakouts = add_breakout_columns(
        index_df,
        components_df
    )

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

    agg_ttm_squeeze = compute_aggregate_ttm_squeeze(
        index_df=index_df,
        components_df=components_df,
        length=None,
        bb_mult=None,
        kc_mult=None,
        use_true_range=None,
        agg_method="median",
    )

    ladder, mini_ladders = mai2.build_vwma_ladders(df_eod_mas, index_df)

    return {
        "close_vol": out_close_vol,
        "hi_lo_diff": hi_lo_diff,
        "adv_dec_indicators": adv_dec_indicators,
        "idx_breakouts": df_idx_breakouts,
        "idx_with_osc": df_idx_with_osc,
        "idx_agg": df_idx_agg,
        "idx_compress": df_idx_compress,
        "comp_compress": df_comp_compress,
        "agg_ttm_squeeze": agg_ttm_squeeze,
        "ladder": ladder,
        "mini_ladders": mini_ladders,
    }


# ----------------------------------------------
# 4. BUILD FIGURES FUNCTION (NO calculations)
# ----------------------------------------------
def build_figures(ps, ps_long, indicators, swing_metrics, df_bcb_daily, usd_series, fileloc):
    figs = []

    # Page 1: Swing Readiness & Momentum
    figs.append(plot_close_vol_obv(ps, indicators["close_vol"]))
    figs.append(plot_aggregate_ttm_squeeze(ps, indicators["agg_ttm_squeeze"]))

    # Page 2: Ignition & Short-Term Impulse
    figs.append(pad.plot_breadth_breakout(indicators["adv_dec_indicators"], ps))
    figs.append(plot_breakouts(ps, indicators["idx_breakouts"]))

    # Page 3: Trend Structure & Health
    figs.append(pmai2.plot_vwma_percent_trends_4panels(ps, indicators["ladder"], indicators["mini_ladders"]))
    figs.append(phi.plot_highs_and_lows(ps, indicators["hi_lo_diff"]))

    # Page 4: Executive Alert & Daytrading Bias Dashboard
    summary_fig = print_and_plot_summary_page(indicators, swing_metrics, ps)
    figs.append(summary_fig)

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


# ---------------------------------------
# 6. Main Execution Pipeline
# ---------------------------------------
def main():
    # Pass the imported file_locations dictionary into load_file_locations_dict
    fileloc = load_file_locations_dict(file_locations)

    # 1. Load market data
    config, update_bcb, index_df, components_df = load_and_align_data(fileloc)
    ps = config.ps

    # 2. Load macro data
    df_bcb_daily, usd_series = load_macro_data(fileloc, index_df.index, update_bcb)

    print("Computing indicators...")
    indicators = compute_indicators(index_df, components_df, ps)

    print("Computing swing metrics (Stockbee 4%, Vol A/D, MA Ratios)...")
    swing_metrics = compute_swing_metrics(components_df, index_df)

    print("Building report figures & printing summary...")
    figs = build_figures(
        ps=index_df,
        ps_long=index_df,
        indicators=indicators,
        swing_metrics=swing_metrics,
        df_bcb_daily=df_bcb_daily,
        usd_series=usd_series,
        fileloc=fileloc,
    )

    print("Exporting PDF...")
    export_pdf_and_open(figs, fileloc, ps)
    print("Done!")

if __name__ == "__main__":
    main()