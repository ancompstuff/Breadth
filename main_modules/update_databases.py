import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from core.constants import yahoo_market_details


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

    market_to_study_dict = config.market_to_study
    market_key = next(iter(market_to_study_dict))
    market_to_study_dict_values = market_to_study_dict[market_key]
    idx_code_to_study = market_to_study_dict_values["idx_code"]
    market_name_to_study = market_to_study_dict_values["market"]

    last_date_to_download = config.download_end_date
    # config.yf_end_date is often T+1, providing the final date for the yfinance API call
    last_yahoo_date_to_download = config.yf_end_date

    # -----------------------
    def update_indexes():
        # ------------------------
        print("\n****************************************************************************")
        print("---------------------- Updating ALL Index files -----------------------------")
        print("****************************************************************************\n")

        index_to_study_df = None
        requested_last_date = datetime.strptime(last_date_to_download, "%Y-%m-%d").date()
        last_yahoo_end_date = datetime.strptime(last_yahoo_date_to_download, "%Y-%m-%d").date()

        for key, info in yahoo_market_details.items():
            idx_code = info["idx_code"]
            idx_path = os.path.join(csv_folder, f"INDEX_{idx_code}.csv")

            try:
                df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
                df.index = pd.to_datetime(df.index, errors="coerce")

                # Ensure data is sorted
                df = df.sort_index()
                df = df[~df.index.duplicated(keep="first")]

                print(f"-------------------- {idx_code} Last row before update -------------------------")
                print(df.tail(1))

                # Drop "last-zero-volume" line if necessary (often incomplete data)
                if not df.empty and "Volume" in df.columns and df["Volume"].iloc[-1] == 0:
                    df = df.iloc[:-1]

                # --- NEW LOGIC: FIND LAST VALID DATE (NOT NaN) ---
                start_update = config.yf_start_date  # Default to start
                last_existing_date = None

                if not df.empty:
                    # Look for the last non-NaN date in the 'Close' or 'Adj Close' column
                    cols_to_check = ['Adj Close', 'Close']
                    last_valid_idx = None
                    for col in cols_to_check:
                        if col in df.columns:
                            last_valid_idx = df[col].last_valid_index()
                            if last_valid_idx is not None:
                                break

                    if last_valid_idx is not None:
                        last_existing_date = last_valid_idx.date()
                        # Start updating FROM the last valid date (overlap) to ensure continuity
                        start_update = last_valid_idx.strftime("%Y-%m-%d")

                if last_existing_date is not None:
                    # Skip only if the last *valid* date in the file covers the requested end date
                    if last_existing_date >= requested_last_date:
                        print(
                            f"-------------------- {idx_code} already up-to-date with requested end date ({requested_last_date}) -------------------------")
                        if idx_code == idx_code_to_study:
                            index_to_study_df = df
                        continue

                        # Also skip if the file date is already >= the YF end date
                    if last_existing_date >= last_yahoo_end_date:
                        print(
                            f"-------------------- {idx_code} already up-to-date with Yahoo end date ({last_yahoo_end_date}) -------------------------")
                        if idx_code == idx_code_to_study:
                            index_to_study_df = df
                        continue

                print(f"Updating {idx_code} from {start_update} to {last_yahoo_date_to_download}")

                new_data = yf.download(idx_code,
                                       start=start_update,
                                       end=last_yahoo_date_to_download,
                                       progress=False,
                                       rounding=True,
                                       auto_adjust=False,
                                       multi_level_index=False
                                       )

                if not new_data.empty:
                    # Clean up columns if single ticker download returned MultiIndex
                    if isinstance(new_data.columns, pd.MultiIndex):
                        new_data = new_data.droplevel(1, axis=1)

                    new_data.index = pd.to_datetime(new_data.index, errors="coerce")

                    # --- ROBUST CONCATENATION LOGIC: New data overwrites old data on overlap ---
                    updated = pd.concat([df, new_data])
                    updated = updated.sort_index()
                    # Crucial: Drop duplicates, keeping the *last* one (which is from new_data, refreshing the row)
                    updated = updated[~updated.index.duplicated(keep="last")]

                    # Filter to the requested end date
                    updated = updated[updated.index.date <= requested_last_date]

                    if not updated.equals(df):  # Check if any change occurred
                        updated.to_csv(idx_path)
                        print(f"----------------- ✔ Saved updated index: {idx_path} -------------")
                        # Refresh df reference for return
                        df = updated
                    else:
                        print(f"-------------- No new unique index data for {idx_code} ---------------")
                else:
                    print(f"-------------- No new index data for {idx_code} ---------------")

                # If this is the market being studied → reload/assign for return
                if idx_code == idx_code_to_study:
                    index_to_study_df = df

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
        requested_last_date = datetime.strptime(last_date_to_download, "%Y-%m-%d").date()
        last_yahoo_end_date = datetime.strptime(last_yahoo_date_to_download, "%Y-%m-%d").date()

        for key, info in config.to_update.items():
            market_name = info["market"]
            comp_path = os.path.join(csv_folder, f"EOD_{market_name}.csv")

            try:
                # Read with header=[0, 1] to capture (Price, Ticker) structure
                comp_df = pd.read_csv(comp_path,
                                      index_col=0,
                                      header=[0, 1],
                                      parse_dates=True
                                      )
                comp_df.index = pd.to_datetime(comp_df.index, errors="coerce")

                # FIX: Sort index immediately
                comp_df = comp_df.sort_index()
                comp_df = comp_df[~comp_df.index.duplicated(keep="first")]

                if comp_df.empty:
                    print(f"{market_name}: no existing component data, skipping.")
                    continue

                print(f"----------------- {market_name} last row before update--------------------")
                print(comp_df.tail(1))

                # --- NEW LOGIC: FIND LAST VALID DATE (NOT NaN ACROSS ALL TICKERS) ---
                start_update_here = config.yf_start_date  # Default to start
                last_existing_date = None

                if not comp_df.empty and isinstance(comp_df.columns, pd.MultiIndex):
                    # 1. Select all 'Adj Close' columns
                    # We look for 'Adj Close' because that's the canonical price data.
                    try:
                        adj_close_df = comp_df.xs('Adj Close', level=0, axis=1, drop_level=False)
                    except KeyError:
                        # Fallback if 'Adj Close' is missing, maybe just use 'Close'
                        adj_close_df = comp_df.xs('Close', level=0, axis=1, drop_level=False)

                    # 2. Find rows where AT LEAST ONE 'Adj Close' value is not NaN (most recent trading day)
                    valid_rows = adj_close_df.notna().any(axis=1)

                    if valid_rows.any():
                        # 3. Get the last index where valid_rows is True
                        last_valid_idx = valid_rows[valid_rows].index[-1]
                        last_existing_date = last_valid_idx.date()

                        # 4. Start updating FROM the last valid date (overlap)
                        start_update_here = last_valid_idx.strftime("%Y-%m-%d")
                    else:
                        # If no valid data in 'Adj Close' (unlikely for existing DB)
                        pass

                        # Check for skipping download
                if last_existing_date is not None:
                    if last_existing_date >= requested_last_date:
                        print(
                            f"-------------------- {market_name} already up-to-date with requested end date ({requested_last_date}) -------------------------")
                        if market_name == market_name_to_study:
                            components_to_study_df = comp_df
                        continue

                    if last_existing_date >= last_yahoo_end_date:
                        print(
                            f"-------------------- {market_name} already up-to-date with Yahoo end date ({last_yahoo_end_date}) -------------------------")
                        if market_name == market_name_to_study:
                            components_to_study_df = comp_df
                        continue

                tickers = comp_df.columns.get_level_values(1).unique().tolist()
                print(f"Updating {market_name} ({len(tickers)} tickers) from {start_update_here}")

                # FIX: Removed group_by="ticker" to match create_databases column structure (Price Type, Ticker)
                comp_new_data = yf.download(tickers,
                                            start=start_update_here,
                                            end=last_yahoo_date_to_download,
                                            progress=False,
                                            rounding=True,
                                            auto_adjust=False,
                                            actions=True)

                if comp_new_data.empty:
                    print(f"--------- No missing component data for {market_name} ----------------")
                else:
                    comp_new_data.index = pd.to_datetime(comp_new_data.index, errors="coerce")

                    # --- ROBUST CONCATENATION LOGIC: New data overwrites old data on overlap ---
                    updated = pd.concat([comp_df, comp_new_data], axis=0)
                    updated = updated.sort_index()
                    # Crucial: Drop duplicates, keeping the *last* one (which is from comp_new_data, refreshing the row)
                    updated = updated[~updated.index.duplicated(keep="last")]

                    # Filter to requested final date (config.download_end_date)
                    updated = updated[updated.index.date <= requested_last_date]

                    if not updated.equals(comp_df):  # Check if any change occurred
                        updated.to_csv(comp_path)
                        print(f"----------- ✔ Components updated: {comp_path} ----------------")
                        # Update reference for return
                        comp_df = updated
                    else:
                        print(f"----------- No new unique data found for {market_name} ----------------")

                if market_name == market_name_to_study:
                    components_to_study_df = comp_df

            except FileNotFoundError:
                print(f"❌ Component file missing: {comp_path}. Skipping.")
            except Exception as e:
                print(f"⚠️ Error updating components for market {market_name}: {e}")

        return components_to_study_df

    # --- CALL THEM HERE ---
    index_df = update_indexes()
    components_df = update_component_csvs()

    # --- Ensure 'Adj Close' exists in returned dataframes ---
    def _ensure_adj_close_index(df):
        if df is None:
            return df
        # Single-level columns: create 'Adj Close' from 'Close' if missing
        if "Adj Close" not in df.columns and "Close" in df.columns:
            df["Adj Close"] = df["Close"]
        return df

    def _ensure_adj_close_components(df):
        if df is None:
            return df
        # MultiIndex columns (first level = field, second level = ticker)
        if isinstance(df.columns, pd.MultiIndex):
            fields = df.columns.get_level_values(0).unique()
            tickers = df.columns.get_level_values(1).unique()
            # Ensure 'Adj Close' exists for every ticker if 'Close' does
            for t in tickers:
                # Use .loc to avoid SettingWithCopyWarning
                if ("Adj Close", t) not in df.columns and ("Close", t) in df.columns:
                    df.loc[:, ("Adj Close", t)] = df.loc[:, ("Close", t)]
                    # Sort columns for consistent order, otherwise multiindex creation might be scrambled
            df = df.sort_index(axis=1)
        else:
            if "Adj Close" not in df.columns and "Close" in df.columns:
                df["Adj Close"] = df["Close"]
        return df

    index_df = _ensure_adj_close_index(index_df)
    components_df = _ensure_adj_close_components(components_df)

    # --- RETURN BOTH ---
    return index_df, components_df