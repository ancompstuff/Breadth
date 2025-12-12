# IMPORT FUNCTIONS
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import os
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

    """# IBOV vs USD + SELIC + IPCA (uses get_idx1_idx2 → BCB_IPCA_SELIC.csv)
    from plotting.plot_idx1_v_idx2 import plot_idx1_v_idx2
    idx1 = "^BVSP"
    idx2 = "BRL=X"
    fig2 = plot_idx1_v_idx2(idx1, idx2, config, fileloc, ps)
    plt.show()"""

    #-------------------------------------------
    # 2: BCB vs IBOV – grid of single-BCB charts
    #-------------------------------------------
    from indicators.bcb_align import forward_fill_bcb_to_daily
    from indicators.get_idx1_idx2 import get_idx1_idx2
    from plotting.plot_bcb_grid import plot_bcb_grid

    # a) Load BCB monthly data
    bcb_monthly_path = os.path.join(
        fileloc.bacen_downloaded_data_folder,
        "bcb_dashboard_monthly.csv",
    )
    df_bcb = pd.read_csv(bcb_monthly_path, index_col="date", parse_dates=True)

    # b) Convert BCB data to DAILY using IBOV calendar (ps_long_lookback)
    df_bcb_daily = forward_fill_bcb_to_daily(df_bcb, ps_long_lookback.price_data.index)

    # c) IBOV + USD with doubled lookback (config_bcb)
    idx1 = "^BVSP"
    idx2 = "BRL=X"
    df_idx_usd_bcb = get_idx1_idx2(idx1, idx2, config_bcb, fileloc, ps_long_lookback)
    df_idx_usd_bcb.index = pd.to_datetime(df_idx_usd_bcb.index)

    # d) USD aligned to ps_long_lookback price index
    src = df_idx_usd_bcb[idx2].sort_index()
    tgt = ps_long_lookback.price_data.index

    # e) First pass: reindex + ffill
    usd_series_bcb = src.reindex(tgt).ffill()

    # f) If still contains NaNs (rare), use merge_asof
    if usd_series_bcb.isna().any():
        left = pd.DataFrame({"t": tgt})
        right = src.reset_index().rename(columns={"index": "t", idx2: "val"})
        merged = pd.merge_asof(
            left.sort_values("t"),
            right.sort_values("t"),
            on="t",
            direction="backward"
        )
        usd_series_bcb = pd.Series(merged["val"].values, index=tgt).ffill()

    # g) Plot grid (display only once, save to PDF later)
    figs_bcb = plot_bcb_grid(
        ps_long_lookback,
        df_bcb_daily,
        usd_series=usd_series_bcb,
        nrows=3,
        ncols=2,
    )
    #for fig in figs_bcb:
    #    fig.show()

    #-------------------
    # 3: BVSP vs Indexes
    #-------------------
    import plotting.plot_bvsp_vs_indexes as ppbi
    figs_bvsp = ppbi.plot_bvsp_vs_all_indices(ps_long_lookback, fileloc, nrows=3, ncols=2)
    #for fig in figs_bvsp:
    #    fig.show()
    #plt.show()


    #---------------------------------------------
    # MAKE PDF -----------------------------------
    #---------------------------------------------
    # Create the output PDF path
    pdf_filename = f"{ps.mkt} breadth_{datetime.today().strftime('%Y-%m-%d')}.pdf"
    pdf_path = os.path.join(fileloc.pdf_folder, pdf_filename)

    # Open the PDF file to save plots (reuse already-generated figures)
    with PdfPages(pdf_path) as pdf:

        pdf.savefig(fig1)
        plt.close(fig1)

        for fig in figs_bcb:
            pdf.savefig(fig)
            plt.close(fig)

        for f in figs_bvsp:
            pdf.savefig(f)
            plt.close(f)

        # -----------------------------------
        # Open PDF automatically if possible
        # -----------------------------------
        if os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)  # For Windows
            except AttributeError:
                os.system(f'open "{pdf_path}"')  # For macOS/Linux
        else:
            print("PDF not generated: ", pdf_path)


###################################
# Main
###################################

if __name__ == "__main__":
    main()
