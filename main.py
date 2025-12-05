# IMPORT FUNCTIONS
import matplotlib.pyplot as plt
import pandas as pd
import os

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

    # 1) Load the file_locations dict
    fileloc = load_file_locations_dict(file_locations)
    print("fileloc.yahoo:", fileloc.yahoo_downloaded_data_folder)
    print("fileloc.bacen:", fileloc.bacen_downloaded_data_folder)
    print("fileloc.pdf:", fileloc.pdf_folder)
    print("fileloc.codes_to_download:", fileloc.codes_to_download_folder)

    # 2) Run the full interactive setup
    config = what_do_you_want_to_do(fileloc)

    # 3) Execute the requested action (update DB or rebuild DBs) and align indexes
    index_df, components_df = update_or_create_databases(config, fileloc)
    index_df, components_df = align_and_prepare_for_plot(index_df, components_df)
    """print(f"index_df last line:\n{index_df.tail(1)}")
       print(f'Index type: {index_df.index.dtype}')
       print(f"components_df last line:\n{components_df.tail(1)}")
       print(f'Index type: {components_df.index.dtype}')"""

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
    ps = prepare_plot_data(index_df, components_df, config)

    ###################################
    # 6) STANDARD PLOTS
    ###################################

    # Close/Volume/OBV
    from plotting.close_vol_obv import plot_close_vol_obv
    fig1 = plot_close_vol_obv(ps, out_df)
    plt.show()

    # IBOV vs USD + SELIC + IPCA
    from plotting.plot_idx1_v_idx2 import plot_idx1_v_idx2
    # Typically idx1 = IBOV and idx2 = USD/BRL
    idx1 = "^BVSP"
    idx2 = "BRL=X"
    fig2 = plot_idx1_v_idx2(idx1, idx2, config, fileloc, ps)
    plt.show()

    ################################################################
    # 1) Load BCB monthly data (example: from CSV you already save)
    ################################################################
    from indicators.bcb_align import bcb_all_vs_ibov_normalized
    from plotting.plot_bcb_vs_yahoo import plot_bcb_vs_yahoo

    import os

    bcb_monthly_path = os.path.join(fileloc.bacen_downloaded_data_folder, "bcb_dashboard_monthly.csv")
    df_bcb = pd.read_csv(bcb_monthly_path, index_col="date", parse_dates=True)

    # 2) Indicator: build normalized daily combined DataFrame
    df_bcb_norm_daily = bcb_all_vs_ibov_normalized(df_bcb, index_df)

    # 3) Plot: BCB vs Yahoo, normalized
    fig3, ax3 = plot_bcb_vs_yahoo(ps, df_bcb_norm_daily)
    plt.show()



###################################
# Main
###################################

if __name__ == "__main__":
    main()
