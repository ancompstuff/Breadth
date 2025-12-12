import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from core.constants import file_locations, yahoo_market_details


def create_databases(config, fileloc):
    """
    Create fresh index and component-level databases for the selected markets.

    Uses ONLY:
        - config (Config dataclass)
        - fileloc (FileLocations dataclass)

    Everything needed comes from these two objects:
        config.market_to_study     → dict {1: {...}}
        config.to_update           → dict of markets to download
        config.first_date_to_download
        config.last_date_to_download
        config.yahoo_end_date
        fileloc.codes_to_download_folder
        fileloc.yahoo_downloaded_data_folder
    """
    #
    config.bcb_series = {
        "ipca": 433,
        "selic": 4390
    }

    #Initialise empty dfs
    index_df = []
    components_df = []
    # ---------------------------------------------------------
    # 1) Prepare folders
    # ---------------------------------------------------------
    os.makedirs(fileloc.yahoo_downloaded_data_folder, exist_ok=True)

    print("\n📂 Creating new databases...")
    print(f"Database folder: {fileloc.yahoo_downloaded_data_folder}")
    print(f"Tickers folder:  {fileloc.codes_to_download_folder}")
    print("-" * 60)

    # ---------------------------------------------------------
    # 2) Iterate over all markets that must be created
    # ---------------------------------------------------------
    for key, info in yahoo_market_details.items():

        idx_code = info["idx_code"]
        market = info["market"]
        #codes_csv_file = info["codes_csv"]
        ##number_tickers = info["number_tickers"]

        print(f"\n=== Building {market} ({idx_code}) ===")
        #print(f"Tickers: {number_tickers}")

        # -----------------------------------------------------
        # 3) Download INDEX data
        # -----------------------------------------------------
        print(f"→ Downloading INDEX: {idx_code}")

        idx_data = yf.download(
            idx_code,
            start=config.yf_start_date,
            end=config.yf_end_date,
            rounding=True,
            auto_adjust=False,  # True: no Adj Close, OHLC adjusted automatically.
            progress=False,
            multi_level_index=False
        )
        #print(f"idx_data.dtypes: {idx_data.dtypes}")

        idx_path = os.path.join(
            fileloc.yahoo_downloaded_data_folder,
            f"INDEX_{idx_code}.csv"
        )
        idx_data.to_csv(idx_path, index=True)
        print(f"Index data saved to: {idx_path}")

        # If this is the market being studied → reload after update
        market_info = next(iter(config.market_to_study.values()))  # Get the first (and only) market info
        if idx_code == market_info['idx_code']:
            index_df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
            index_df.index = pd.to_datetime(index_df.index, errors="coerce")
            index_df = index_df[~index_df.index.duplicated(keep="first")]

    # -----------------------------------------------------
    # 4) Load tickers
    # -----------------------------------------------------
    for key, info in config.to_update.items():
        market = info["market"]
        #idx_code = info["idx_code"]
        codes_csv_file = info["codes_csv"]
        #number_tickers = info["number_tickers"]

        # CSV containing the component tickers
        tickers_csv_path = os.path.join(
            fileloc.codes_to_download_folder,
            codes_csv_file
        )
        if not os.path.exists(tickers_csv_path):
            print(f"❌ Missing CSV: {tickers_csv_path}")
            continue
        tickers = pd.read_csv(f"{tickers_csv_path}")["Code"].dropna().unique().tolist()

        # -----------------------------------------------------
        # 5) Download COMPONENTS
        # -----------------------------------------------------
        print("→ Downloading COMPONENT tickers...")
        comp_data = yf.download(
            tickers,
            start=config.yf_start_date,
            end=config.yf_end_date,
            interval="1d",
            actions=True,
            auto_adjust=False,
            rounding=True,
            #group_by="ticker",
            progress=False
        )

        comp_path = os.path.join(
            fileloc.yahoo_downloaded_data_folder,
            f"EOD_{market}.csv"
        )

        comp_data.to_csv(comp_path)
        print(f"Saved: {comp_path}")

        market_info = next(iter(config.market_to_study.values()))  # Get the first (and only) market info
        if market == market_info['market']:
            components_df = pd.read_csv(comp_path,
                                       index_col=0,
                                       header=[0, 1],
                                       parse_dates=True
                                       )
            components_df.index = pd.to_datetime(
                components_df.index,
                errors="coerce"
            )
            components_df = (
                components_df)[~components_df.index.duplicated(keep="first")
            ]

    print("\n✅ Database creation completed.")

    """# ----------------------------------------------------------
    #   DOWNLOAD / UPDATE BCB DATA FOR SAME DATE RANGE
    # ----------------------------------------------------------
    print("\n***************************************************************")
    print("--------------- Downloading BCB (IPCA / SELIC / others) -------")
    print("***************************************************************\n")

    # Here we just call the BCB DB function with same dates as Yahoo:
    create_or_update_bcb_database(
        fileloc_bacen_downloaded_data_folder=fileloc.bacen_downloaded_data_folder,
        yf_start_date=config.yf_start_date,
        yf_end_date=config.yf_end_date,
        series_map=bcb_series_catalog,  # bcb_default_series,  # or any other dict if you want more series
        filename="BCB_IPCA_SELIC.csv",  # keep same for compatibility
        use_subfolder=False  # or True if you prefer bacen_data/bcb/
    )
"""
    return index_df, components_df
##################################################################################################
# Main for testing
##################################################################################################

if __name__ == "__main__":
    from core.my_data_types import load_file_locations_dict, Config

    fileloc = load_file_locations_dict(file_locations)

    cfg = Config(
        to_do=5,
        market_to_study= {13: {'idx_code': '^BVSP', 'market': '3 ticker test', 'codes_csv': 'TEST.csv', "number_tickers":3}},
        to_update={13: {'idx_code': '^BVSP', 'market': '3 ticker test', 'codes_csv': 'TEST.csv', "number_tickers":3}},
        graph_lookback=252,
        yf_start_date="2020-01-01",
        download_end_date=datetime.now().strftime("%Y-%m-%d"),
        yf_end_date=datetime.now().strftime("%Y-%m-%d"),
        study_end_date=datetime.now().strftime("%Y-%m-%d")
    )
    create_databases(cfg, fileloc)