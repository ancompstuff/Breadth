# IMPORT FUNCTIONS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import os
import time
from dataclasses import replace
from datetime import datetime

from core.constants import file_locations
from core.my_data_types import load_file_locations_dict
from main_modules.user_setup import what_do_you_want_to_do
from main_modules.update_or_create import update_or_create_databases
from utils.align_dataframes import align_and_prepare_for_plot

#############################################
# main.py — Central dispatcher for Structured_Breadth
#############################################
"""
Responsibilities:
-----------------
1. Load file location settings from core/file_locations.json
2. Run interactive user setup and return a Config object
3. Dispatch to the correct action: update or create databases
4. (Later) plot charts, generate PDFs, etc.
"""

def main():

    #--------------------------------
    # 1) Load the file_locations dict
    #--------------------------------
    fileloc = load_file_locations_dict(file_locations)
    print("fileloc.yahoo:", fileloc.yahoo_downloaded_data_folder)
    print("fileloc.bacen:", fileloc.bacen_downloaded_data_folder)
    print("fileloc.pdf:", fileloc.pdf_folder)
    print("fileloc.codes_to_download:", fileloc.codes_to_download_folder)

    #----------------------------------
    # 2) Run the full interactive setup
    #----------------------------------
    config = what_do_you_want_to_do(fileloc)

    # Update BCB data or not (monthly and takes a while)
    from utils.update_bcb_y_or_n import ask_update_bcb
    update_bcb = ask_update_bcb()

    #-----------------------------------------------------------------------------
    # 3) Execute the requested action (update DB or rebuild DBs) and align indexes
    #-----------------------------------------------------------------------------
    index_df, components_df = update_or_create_databases(config, fileloc)
    index_df, components_df = align_and_prepare_for_plot(index_df, components_df)
    """print(f"index_df last line:\n{index_df.tail(1)}")
       print(f'Index type: {index_df.index.dtype}')
       print(f"components_df last line:\n{components_df.tail(1)}")
       print(f'Index type: {components_df.index.dtype}')"""

    #-----------------------
    # 3) Build BCB files
    #-----------------------
    if update_bcb:
        from main_modules.build_bcb_files import build_bcb_files
        build_bcb_files(fileloc)
    else:
        print("BCB update skipped. Using existing BCB data.")

    ###################################
    # 4) Indicator calculations
    ###################################

    # Close/Volume/OBV
    from indicators.close_vol_obv import compute_close_vol_obv
    out_df = compute_close_vol_obv(index_df)

    ###################################
    # 5) PlotSetup creation
    ###################################
    from plotting.common_plot_setup import prepare_plot_data

    # 1) Normal PlotSetup
    ps = prepare_plot_data(index_df, components_df, config)
    #print("price_data columns:", ps.price_data.columns.tolist())

    ## 2) BCB PlotSetup with 2× lookback
    config_bcb = replace(config, graph_lookback=config.graph_lookback * 5)
    ps_long_lookback = prepare_plot_data(index_df, components_df, config_bcb)

    ###################################
    # 6) STANDARD PLOTS
    ###################################

    #--------------------
    # 1: Close/Volume/OBV
    #--------------------
    from plotting.plot_close_vol_obv import plot_close_vol_obv
    fig1 = plot_close_vol_obv(ps, out_df)
    #plt.show()

    # -------------------------------------------
    # 2: BCB vs IBOV – grid of single-BCB charts
    # -------------------------------------------
    from utils.load_usd_from_files import load_usd_series
    from plotting.plot_bcb_grid import plot_bcb_grid

    # a) Prefer TRADING-ALIGNED file if it exists
    bcb_ready_trading_path = os.path.join(
        fileloc.bacen_downloaded_data_folder,
        "bcb_dashboard_ready_trading.csv",
    )
    bcb_ready_path = os.path.join(
        fileloc.bacen_downloaded_data_folder,
        "bcb_dashboard_ready.csv",
    )

    if os.path.exists(bcb_ready_trading_path):
        print("[BCB] Using trading-aligned ready file.")
        df_bcb = pd.read_csv(bcb_ready_trading_path, index_col="date", parse_dates=True)
    else:
        print("[BCB] Using calendar ready file.")
        df_bcb = pd.read_csv(bcb_ready_path, index_col="date", parse_dates=True)

    # b) Ensure BCB is aligned to trading calendar
    tgt = ps_long_lookback.price_data.index
    df_bcb_daily = df_bcb.reindex(tgt).ffill()

    # c) Load USD from local CSV
    usd_raw = load_usd_series(fileloc)

    # d) Align USD to trading calendar
    usd_series_bcb = usd_raw.reindex(tgt).ffill()

    # (Optional): merge_asof safety repair
    if usd_series_bcb.isna().any():
        left = pd.DataFrame({"t": tgt})
        right = usd_raw.reset_index().rename(columns={"index": "t", usd_raw.name: "val"})
        merged = pd.merge_asof(
            left.sort_values("t"),
            right.sort_values("t"),
            on="t",
            direction="backward",
        )
        usd_series_bcb = pd.Series(merged["val"].values, index=tgt).ffill()

    # e) Plot grid
    figs = plot_bcb_grid(
        ps_long_lookback,
        df_bcb_daily,
        usd_series=usd_series_bcb,
        nrows=3,
        ncols=2,
    )

    #-------------------
    # 3: BVSP vs Indexes
    #-------------------
    import plotting.plot_bvsp_vs_indexes as ppbi
    figs = ppbi.plot_bvsp_vs_all_indices(ps_long_lookback, fileloc, nrows=3, ncols=2)
    #for fig in figs:
    #    fig.show()
    #plt.show()

    # -------------------
    # 3: MA/ VWMA vs Indexes
    # -------------------
    from main_modules.create_databases import create_databases  # or update_databases
    import indicators.ma_indicators as mai
    import plotting.plot_ma_indicators_1 as pmai

    df_idx_mas, df_eod_mas = mai.calculate_idx_and_comp_ma_vwma(index_df, components_df)
    df_idx_with_osc = mai.calculate_ma_vwma_max_min(df_idx_mas, ps)
    df_idx_agg = mai.calculate_tickers_over_under_mas(df_idx_mas, df_eod_mas, ps)
    df_idx_compress, df_comp_compress = mai.calculate_compressao_dispersao(df_idx_mas, df_eod_mas)

    #---------------------------------------------
    # MAKE PDF -----------------------------------
    #---------------------------------------------
    # Create the output PDF path
    pdf_filename = f"{ps.mkt} breadth_{datetime.today().strftime('%Y-%m-%d')}.pdf"
    pdf_path = os.path.join(fileloc.pdf_folder, pdf_filename)

    # Open the PDF file to save plots
    with PdfPages(pdf_path) as pdf:

        fig1 = plot_close_vol_obv(ps, out_df)
        pdf.savefig(fig1)
        plt.close(fig1)

        figs_2 = plot_bcb_grid(
            ps_long_lookback,
            df_bcb_daily,
            usd_series=usd_series_bcb,
            nrows=3,
            ncols=2,
        )
        for fig in figs_2:
            pdf.savefig(fig)
            plt.close(fig)

        figs_3 = ppbi.plot_bvsp_vs_all_indices(ps_long_lookback, fileloc, nrows=3, ncols=2)
        for fig in figs_3:
            pdf.savefig(fig)
            plt.close(fig)

        fig4 = pmai.plot_index_vs_ma_vwma(df_idx_with_osc, ps)
        pdf.savefig(fig4)
        plt.close(fig4)
        fig5 = pmai.plot_tickers_over_under_mas(df_idx_agg, ps)
        pdf.savefig(fig5)
        plt.close(fig5)
        #fig6 = pmai.plot_compression_dispersion(df_idx_compress, df_comp_compress, ps)
        #pdf.savefig(fig6)
        #plt.close(fig6)
        fig6 = pmai.plot_absolute_compression_bands(df_idx_compress, df_comp_compress, ps)
        pdf.savefig(fig6)
        plt.close(fig6)

    # *** CRITICAL: The file is closed here ***
    # Introduce a small delay to ensure the OS releases the file lock
    time.sleep(0.5)  # Wait for half a second (0.1 to 1.0 second is usually enough)

    # -----------------------------------
    # Open PDF automatically if possible
    # -----------------------------------
    if os.path.exists(pdf_path):
        try:
            os.startfile(pdf_path)  # For Windows
        except AttributeError:
            os.system(f'open "{pdf_path}"')  # For macOS/Linux
        except FileNotFoundError:
            # This handles cases where the path is valid but the file still isn't fully ready
            print(f"Error: Could not find or open file {pdf_path}. Try opening manually.")
    else:
        print("PDF not generated: ", pdf_path)

###################################
# Main
###################################

if __name__ == "__main__":
    main()
