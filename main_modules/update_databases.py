import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from core.constants import yahoo_market_details
from main_modules.bcb_data import download_and_save_bcb


# ======================================================================
#   UPDATE INDEX + COMPONENTS USING NEW CONFIG + FILELOC STRUCTURE
# ======================================================================

def update_databases(config, fileloc):
    """
    Update existing databases using the SAME config + fileloc structure
    used by user_setup and create_databases.

    INPUTS:
        config   → Config dataclass
        fileloc  → FileLocations dataclass

    RETURNS:
        (index_df, components_df)  for the selected market_to_study_dict_values
    """
    # Location of all CSV files
    csv_folder = fileloc.yahoo_downloaded_data_folder

    market_to_study_dict = config.market_to_study  # p.ex: 1: {"market": "Brazil", "idx_code": "^BVSP", "codes_csv": "IBOV.csv"}
    market_key = next(iter(market_to_study_dict))  # p.ex: 1
    market_to_study_dict_values = market_to_study_dict[market_key]  # p.ex: {"market": "Brazil", "idx_code": "^BVSP", "codes_csv": "IBOV.csv"}
    idx_code_to_study = market_to_study_dict_values["idx_code"]
    market_name_to_study = market_to_study_dict_values["market"]

    last_date_to_download = config.download_end_date
    last_yahoo_date_to_download = config.yf_end_date

    # -----------------------
    def update_indexes():
    #------------------------
        print("\n****************************************************************************")
        print("---------------------- Updating ALL Index files -----------------------------")
        print("****************************************************************************\n")

        index_to_study_df = None
        # "key"! is the integer market key,
        # value the dictionary: "idx_code": "^BVSP", "market": "Bovespa", "codes_csv": "IBOV.csv", "number_tickers": 82}
        for key, info in yahoo_market_details.items():
            idx_code = info["idx_code"]
            idx_path = os.path.join(csv_folder, f"INDEX_{idx_code}.csv")

            try:
                df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
                df.index = pd.to_datetime(df.index, errors="coerce")
                df = df[~df.index.duplicated(keep="first")]
                print(f"-------------------- {idx_code} Last row before update -------------------------")
                print(df.tail(1))

                # Drop "last-zero-volume" line if necessary
                if df["Volume"].iloc[-1] == 0:
                    df = df.iloc[:-1]

                # Get last date in csv to start update
                start_update_here = df.index[-1] + timedelta(days=1)
                start_update = start_update_here.strftime("%Y-%m-%d")

                # Check not already up to date
                requested_last_date = datetime.strptime(last_date_to_download, "%Y-%m-%d").date()
                if df.index[-1].date() >= requested_last_date:
                    print(f"-------------------- {idx_code} already up-to-date -------------------------")

                else:
                    print(f"Updating {idx_code} from {start_update} to {last_yahoo_date_to_download}")

                    new_data = yf.download(idx_code,
                                           start=start_update,
                                           end=last_yahoo_date_to_download,
                                           progress=False,  # show progress bar
                                           rounding=True,
                                           auto_adjust=True
                                           )

                    if not new_data.empty:
                        if isinstance(new_data.columns, pd.MultiIndex):
                            new_data = new_data.droplevel(1, axis=1)

                        new_data.index = pd.to_datetime(new_data.index, errors="coerce")
                        updated = pd.concat([df, new_data])
                        updated = updated[~updated.index.duplicated(keep="first")]
                        updated.to_csv(idx_path)
                        print(f"----------------- ✔ Saved updated index: {idx_path} -------------")
                    else:
                        print(f"-------------- No new index data for {idx_code} ---------------")

                # If this is the market being studied → reload after update
                if idx_code == idx_code_to_study:
                    index_to_study_df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
                    index_to_study_df.index = pd.to_datetime(index_to_study_df.index, errors="coerce")
                    index_to_study_df = index_to_study_df[~index_to_study_df.index.duplicated(keep="first")]

            except FileNotFoundError:
                print(f"❌ Index file missing: {idx_path}. Skipping.")
            except Exception as e:
                print(f"⚠️ Error updating index {idx_code}: {e}")

        return index_to_study_df


    # -----------------------
    def update_component_csvs():
    # ------------------------
        print("\n*******************************************************************************")
        print("--------------------- Updating requested component file(s) ------------------------")
        print("*********************************************************************************\n")
        components_to_study_df = None

        for key, info in config.to_update.items():
            market_name = info["market"]
            comp_path = os.path.join(csv_folder, f"EOD_{market_name}.csv")

            try:
                comp_df = pd.read_csv(comp_path,
                                      index_col=0,
                                      header=[0, 1],
                                      parse_dates=True
                                      )
                comp_df.index = pd.to_datetime(comp_df.index, errors="coerce")
                comp_df = comp_df[comp_df.index.notna()]
                comp_df = comp_df[~comp_df.index.duplicated(keep="first")]
                if comp_df.empty:
                    print(f"{market_name}: no existing component data, skipping.")
                    continue

                print(f"----------------- {market_name} last row before update--------------------")
                print(comp_df.tail(1))

                last_existing = comp_df.index[-1].date()
                requested_last_date = datetime.strptime(last_date_to_download, "%Y-%m-%d").date()
                if  last_existing >= requested_last_date:
                    print(f"-------------------- {market_name} already up-to-date -------------------------")

                else:
                    tickers = comp_df.columns.get_level_values(1).unique().tolist()
                    start_update_here = (last_existing + timedelta(days=1)).strftime("%Y-%m-%d")

                    print(f"Updating {market_name} ({len(tickers)} tickers)")

                    comp_new_data = yf.download(tickers,
                                          start=start_update_here,
                                          end=last_yahoo_date_to_download,
                                          group_by="ticker",
                                          progress=False,
                                          rounding=True,
                                          auto_adjust=True,
                                          actions=True)

                    if comp_new_data.empty:
                        print(f"--------- No missing component data for {market_name} ----------------")
                    else:
                        comp_new_data.index = pd.to_datetime(comp_new_data.index, errors="coerce")
                        updated = pd.concat([comp_df, comp_new_data], axis=0)
                        updated = updated[~updated.index.duplicated(keep="first")].sort_index()
                        updated.to_csv(comp_path)
                        print(f"----------- ✔ Components updated: {comp_path} ----------------")

                if market_name == market_name_to_study:
                    components_to_study_df = pd.read_csv(comp_path,
                                                         index_col=0,
                                                         header=[0, 1],
                                                         parse_dates=True
                                                         )
                    components_to_study_df.index = pd.to_datetime(
                        components_to_study_df.index,
                        errors="coerce"
                    )
                    components_to_study_df = (
                        components_to_study_df)[~components_to_study_df.index.duplicated(keep="first")
                    ]

            except FileNotFoundError:
                print(f"❌ Component file missing: {comp_path}. Skipping.")
            except Exception as e:
                print(f"⚠️ Error updating components for market {market_name}: {e}")

        return components_to_study_df

    # --- CALL THEM HERE ---
    index_df = update_indexes()
    components_df = update_component_csvs()

    # ----------------------------------------------------------
    #   DOWNLOAD SELIC + IPCA FROM BCB FOR SAME DATE RANGE
    # ----------------------------------------------------------
    print("\n***************************************************************")
    print("--------------- Updating SELIC / IPCA (BCB) data --------------")
    print("***************************************************************\n")

    # Convert YYYY-mm-dd → dd/mm/YYYY
    def _to_ddmmyyyy(s):
        if '/' in s:
            return s  # already dd/mm/yyyy
        yyyy, mm, dd = s.split('-')
        return f"{dd}/{mm}/{yyyy}"

    start_bcb = _to_ddmmyyyy(config.yf_start_date)
    end_bcb   = _to_ddmmyyyy(config.yf_end_date)

    # config.bcb_series was added to your Config class:
    #  {"ipca":433, "selic":4390}
    series_map = {
        config.bcb_series["ipca"]: "IPCA",
        config.bcb_series["selic"]: "SELIC"
    }

    download_and_save_bcb(
        fileloc_downloaded_data_folder=fileloc.bacen_downloaded_data_folder,
        start_date=start_bcb,
        end_date=end_bcb,
        series_map=series_map
    )

    # --- RETURN BOTH ---
    return index_df, components_df
