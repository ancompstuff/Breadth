import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


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
        (index_df, components_df)  for the selected market_to_study
    """

    database_folder = fileloc.downloaded_data_folder

    market_to_study_dict = config.market_to_study  # p.ex: 1: {"market": "Brazil", "idx_code": "^BVSP", "codes_csv": "IBOV.csv"}
    market_key = next(iter(market_to_study_dict))  # p.ex: 1
    market_to_study = market_to_study_dict[market_key]  # p.ex: {"market": "Brazil", "idx_code": "^BVSP", "codes_csv": "IBOV.csv"}

    idx_code_to_study = market_to_study["idx_code"]
    market_name_to_study = market_to_study["market"]


    last_date = config.last_date_to_download
    yahoo_end_date = config.yahoo_end_date

    # Values to return
    index_to_study_df = None
    components_to_study_df = None

    print("\n****************************************************************************")
    print("----------------------- UPDATING INDEX DATABASES ----------------------------")
    print("****************************************************************************\n")

    # ==================================================================
    # UPDATE INDEX FILES
    # ==================================================================
    for key, info in config.to_update.items():

        idx_code = info["idx_code"]
        idx_path = os.path.join(database_folder, f"INDEX_{idx_code}.csv")

        try:
            df = pd.read_csv(idx_path, index_col=0, parse_dates=True)

            df.index = pd.to_datetime(df.index, errors="coerce")
            df = df[~df.index.duplicated(keep="first")]

            print("\n----------------------------------------------------------")
            print(f"Updating INDEX: {idx_code}")
            print("Last 2 rows before update:")
            print(df.tail(2))
            print("----------------------------------------------------------")

            update_index_database(
                idx_code=idx_code,
                df=df,
                last_date=last_date,
                yahoo_end_date=yahoo_end_date,
                database_folder=database_folder,
            )

            # If this is the market being studied → reload after update
            if idx_code == idx_code_to_study:
                index_to_study_df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
                index_to_study_df.index = pd.to_datetime(index_to_study_df.index, errors="coerce")
                index_to_study_df = index_to_study_df[~index_to_study_df.index.duplicated(keep="first")]

        except FileNotFoundError:
            print(f"❌ Index file missing: {idx_path}. Skipping.")
        except Exception as e:
            print(f"⚠️ Error updating index {idx_code}: {e}")

    # ==================================================================
    # UPDATE COMPONENTS
    # ==================================================================
    print("\n****************************************************************************")
    print("--------------------- UPDATING COMPONENTS DATABASES --------------------------")
    print("****************************************************************************\n")

    for key, info in config.to_update.items():

        market_name = info["market"]
        csv_file = info["codes_csv"]

        if csv_file == "none":
            continue

        comp_path = os.path.join(database_folder, f"EOD_{market_name}.csv")

        try:
            com_df = pd.read_csv(comp_path, index_col=0, header=[0, 1], parse_dates=True)

            com_df.index = pd.to_datetime(com_df.index, errors="coerce")
            com_df = com_df[com_df.index.notna()]
            com_df = com_df[~com_df.index.duplicated(keep="first")]

            print("\n----------------------------------------------------------")
            print(f"Updating COMPONENTS for: {market_name}")
            print("Last 2 rows before update:")
            print(com_df.tail(2))
            print("----------------------------------------------------------")

            update_components_database(
                market_name=market_name,
                com_df=com_df,
                last_date=last_date,
                yahoo_end_date=yahoo_end_date,
                database_folder=database_folder
            )

            if market_name == market_name_to_study:
                components_to_study_df = pd.read_csv(
                    comp_path, index_col=0, header=[0, 1], parse_dates=True
                )
                components_to_study_df.index = pd.to_datetime(
                    components_to_study_df.index, errors="coerce"
                )
                components_to_study_df = components_to_study_df[
                    ~components_to_study_df.index.duplicated(keep="first")
                ]

        except FileNotFoundError:
            print(f"❌ Component file missing: {comp_path}. Skipping.")
        except Exception as e:
            print(f"⚠️ Error updating components for market {market_name}: {e}")

    return index_to_study_df, components_to_study_df


# ======================================================================
# INTERNAL HELPERS
# ======================================================================

def update_index_database(idx_code, df, last_date, yahoo_end_date, database_folder):
    """Download missing index data and patch CSV."""
    idx_file = os.path.join(database_folder, f"INDEX_{idx_code}.csv")

    # Drop "last-zero-volume" line if necessary
    if df["Volume"].iloc[-1] == 0:
        df = df.iloc[:-1]

    start_next = df.index[-1] + timedelta(days=1)
    start_next_str = start_next.strftime("%Y-%m-%d")

    requested_last = datetime.strptime(last_date, "%Y-%m-%d").date()

    if df.index[-1].date() >= requested_last:
        print(f"{idx_code} already up-to-date.")

        return

    print(f"Updating {idx_code} from {start_next_str} to {yahoo_end_date}")

    new_data = yf.download(idx_code, start=start_next_str, end=yahoo_end_date, progress=False)

    if not new_data.empty:
        if isinstance(new_data.columns, pd.MultiIndex):
            new_data = new_data.droplevel(1, axis=1)

        new_data.index = pd.to_datetime(new_data.index, errors="coerce")

        updated = pd.concat([df, new_data])
        updated = updated[~updated.index.duplicated(keep="first")]

        updated.to_csv(idx_file)
        print(f"✔ Saved updated index: {idx_file}")
    else:
        print(f"No new index data for {idx_code}")


def update_components_database(market_name, com_df, last_date, yahoo_end_date, database_folder):
    """Download missing components data for all tickers."""
    comp_path = os.path.join(database_folder, f"EOD_{market_name}.csv")

    last_existing = com_df.index[-1].date()
    requested_last = datetime.strptime(last_date, "%Y-%m-%d").date()

    if last_existing >= requested_last:
        print(f"{market_name} already up-to-date.")
        return

    tickers = com_df.columns.get_level_values(1).unique().tolist()

    start_next = (last_existing + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Downloading missing components for {market_name} ({len(tickers)} tickers)")
    missing = yf.download(tickers, start=start_next, end=yahoo_end_date, group_by="ticker", progress=False)

    if missing.empty:
        print(f"No missing component data for {market_name}")
        return

    missing.index = pd.to_datetime(missing.index, errors="coerce")

    updated = pd.concat([com_df, missing], axis=0)
    updated = updated[~updated.index.duplicated(keep="first")].sort_index()

    updated.to_csv(comp_path)
    print(f"✔ Components updated: {comp_path}")
