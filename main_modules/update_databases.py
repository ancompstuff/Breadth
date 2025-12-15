import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from core.constants import yahoo_market_details


# ======================================================================
#   HELPER FUNCTIONS FOR EFFICIENCY
# ======================================================================

def _parse_dates_once(download_end_date, yf_end_date):
    """Parse date strings once and reuse throughout the function."""
    requested_last_date = datetime.strptime(download_end_date, "%Y-%m-%d").date()
    last_yahoo_end_date = datetime.strptime(yf_end_date, "%Y-%m-%d").date()
    return requested_last_date, last_yahoo_end_date


def _clean_dataframe(df):
    """Consolidate DataFrame cleaning operations.
    
    Note: Creates a copy to avoid modifying the original DataFrame.
    """
    # Create a copy to avoid side effects
    df = df.copy()
    if df.empty:
        return df
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df


def _find_last_valid_date(df, column_priority=None):
    """Find the last valid (non-NaN) date in a DataFrame efficiently."""
    if df is None or df.empty:
        return None
    
    if column_priority is None:
        column_priority = ['Adj Close', 'Close']
    
    for col in column_priority:
        if col in df.columns:
            last_valid_idx = df[col].last_valid_index()
            if last_valid_idx is not None:
                return last_valid_idx.date()
    return None


def _find_last_valid_date_multiindex(df):
    """Find the last valid date for MultiIndex DataFrame (components)."""
    if df is None or df.empty or not isinstance(df.columns, pd.MultiIndex):
        return None
    
    try:
        adj_close_df = df.xs('Adj Close', level=0, axis=1, drop_level=False)
    except KeyError:
        try:
            adj_close_df = df.xs('Close', level=0, axis=1, drop_level=False)
        except KeyError:
            return None
    
    valid_rows = adj_close_df.notna().any(axis=1)
    if valid_rows.any():
        return valid_rows[valid_rows].index[-1].date()
    return None


def _should_skip_update(last_existing_date, requested_last_date, last_yahoo_end_date):
    """Check if update should be skipped based on existing data dates.
    
    Updates are skipped when the existing data already covers the requested time period.
    This happens when:
    - The last valid data date >= requested end date (we already have all requested data)
    - OR the last valid data date >= Yahoo Finance end date (API won't return newer data)
    
    Args:
        last_existing_date: Last valid date in the existing dataset
        requested_last_date: User's requested end date for the dataset
        last_yahoo_end_date: End date for Yahoo Finance API calls (often requested_date + 1)
    
    Returns:
        bool: True if update should be skipped, False otherwise
    """
    if last_existing_date is None:
        return False
    return (last_existing_date >= requested_last_date or 
            last_existing_date >= last_yahoo_end_date)


def _merge_and_update_data(old_df, new_data, requested_last_date):
    """Merge old and new data efficiently, handling overlaps.
    
    Returns:
        tuple: (updated_df, changed) where changed is True if data was modified
    """
    # Create a copy to avoid modifying the original new_data
    new_data = new_data.copy()
    
    # Clean new data first
    new_data.index = pd.to_datetime(new_data.index, errors="coerce")
    
    # Handle MultiIndex columns for single ticker downloads
    if isinstance(new_data.columns, pd.MultiIndex):
        new_data = new_data.droplevel(1, axis=1)
    
    # Check if new data is empty after cleaning
    if new_data.empty:
        return old_df, False
    
    # Merge: new data overwrites old on overlap
    updated = pd.concat([old_df, new_data])
    updated = updated.sort_index()
    updated = updated[~updated.index.duplicated(keep="last")]
    
    # Filter to requested end date
    updated = updated[updated.index.date <= requested_last_date]
    
    # Check if any change occurred
    changed = not updated.equals(old_df)
    return updated, changed


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

    # Parse dates once at the beginning
    requested_last_date, last_yahoo_end_date = _parse_dates_once(
        config.download_end_date, config.yf_end_date
    )

    # -----------------------
    def update_indexes():
        # ------------------------
        print("\n****************************************************************************")
        print("---------------------- Updating ALL Index files -----------------------------")
        print("****************************************************************************\n")

        index_to_study_df = None

        for key, info in yahoo_market_details.items():
            idx_code = info["idx_code"]
            idx_path = os.path.join(csv_folder, f"INDEX_{idx_code}.csv")

            try:
                df = pd.read_csv(idx_path, index_col=0, parse_dates=True)
                df = _clean_dataframe(df)

                print(f"-------------------- {idx_code} Last row before update -------------------------")
                print(df.tail(1))

                # Drop "last-zero-volume" line if necessary (often incomplete data)
                if not df.empty and "Volume" in df.columns and df["Volume"].iloc[-1] == 0:
                    df = df.iloc[:-1]

                # Find last valid date efficiently
                last_existing_date = _find_last_valid_date(df)
                
                # Determine start update date
                start_update = config.yf_start_date
                if last_existing_date is not None:
                    start_update = last_existing_date.strftime("%Y-%m-%d")

                # Check if update should be skipped
                if _should_skip_update(last_existing_date, requested_last_date, last_yahoo_end_date):
                    if last_existing_date >= requested_last_date:
                        print(f"-------------------- {idx_code} already up-to-date with requested end date ({requested_last_date}) -------------------------")
                    else:
                        print(f"-------------------- {idx_code} already up-to-date with Yahoo end date ({last_yahoo_end_date}) -------------------------")
                    if idx_code == idx_code_to_study:
                        index_to_study_df = df
                    continue

                print(f"Updating {idx_code} from {start_update} to {config.yf_end_date}")

                new_data = yf.download(idx_code,
                                       start=start_update,
                                       end=config.yf_end_date,
                                       progress=False,
                                       rounding=True,
                                       auto_adjust=False,
                                       multi_level_index=False
                                       )

                updated, changed = _merge_and_update_data(df, new_data, requested_last_date)
                
                if changed:
                    updated.to_csv(idx_path)
                    print(f"----------------- ✔ Saved updated index: {idx_path} -------------")
                    df = updated
                else:
                    # No changes could be due to empty new_data or no new unique data
                    if new_data.empty:
                        print(f"-------------- No new index data for {idx_code} ---------------")
                    else:
                        print(f"-------------- No new unique index data for {idx_code} ---------------")

                # If this is the market being studied → assign for return
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
                comp_df = _clean_dataframe(comp_df)

                if comp_df.empty:
                    print(f"{market_name}: no existing component data, skipping.")
                    continue

                print(f"----------------- {market_name} last row before update--------------------")
                print(comp_df.tail(1))

                # Find last valid date efficiently
                last_existing_date = _find_last_valid_date_multiindex(comp_df)
                
                # Determine start update date
                start_update_here = config.yf_start_date
                if last_existing_date is not None:
                    start_update_here = last_existing_date.strftime("%Y-%m-%d")

                # Check if update should be skipped
                if _should_skip_update(last_existing_date, requested_last_date, last_yahoo_end_date):
                    if last_existing_date >= requested_last_date:
                        print(f"-------------------- {market_name} already up-to-date with requested end date ({requested_last_date}) -------------------------")
                    else:
                        print(f"-------------------- {market_name} already up-to-date with Yahoo end date ({last_yahoo_end_date}) -------------------------")
                    if market_name == market_name_to_study:
                        components_to_study_df = comp_df
                    continue

                tickers = comp_df.columns.get_level_values(1).unique().tolist()
                print(f"Updating {market_name} ({len(tickers)} tickers) from {start_update_here}")

                comp_new_data = yf.download(tickers,
                                            start=start_update_here,
                                            end=config.yf_end_date,
                                            progress=False,
                                            rounding=True,
                                            auto_adjust=False,
                                            actions=True)

                if comp_new_data.empty:
                    print(f"--------- No missing component data for {market_name} ----------------")
                else:
                    # Use the same merge logic as indexes for consistency
                    updated, changed = _merge_and_update_data(comp_df, comp_new_data, requested_last_date)
                    
                    if changed:
                        updated.to_csv(comp_path)
                        print(f"----------- ✔ Components updated: {comp_path} ----------------")
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