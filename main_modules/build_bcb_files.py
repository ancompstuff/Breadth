"""
build_bcb_files.py

High-level builder that uses bcb_fetcher.fetch_series to download all series,
merge them, and write:
 - bcb_dashboard_raw.csv       (raw merged)
 - bcb_dashboard_monthly.csv   (month-end)
 - bcb_dashboard_ready.csv     (calendar daily, forward-filled)
 - bcb_dashboard_ready_trading.csv (if IBOV index available: reindexed to trading dates)

Usage:
    from main_modules.build_bcb_files import build_bcb_files
    build_bcb_files(fileloc, force_full_refresh=False)
"""
import os
from datetime import date, timedelta
import pandas as pd

from core.constants import file_locations
from core.my_data_types import load_file_locations_dict
from core.bcb_config import BCB_SGS_SERIES  

# Use the fetcher we just created
from main_modules.bcb_fetcher import fetch_series

# defaults
START_DATE = date(2010, 1, 1)
END_DATE = date.today()
DEFAULT_MAX_YEARS_PER_REQUEST = 10

def build_bcb_files(fileloc, force_full_refresh: bool = False, debug: bool = True):
    """
    Build BCB datasets:
      - raw (merged)
      - monthly (ME)
      - ready (daily forward-filled calendar)
      - ready_trading (if IBOV trading index found)

    Parameters:
      fileloc: object/dict with attributes:
          - bacen_downloaded_data_folder (where CSVs are saved)
          - yahoo (optional) path used to find INDEX_^BVSP.csv for trading calendar
      force_full_refresh: if True, ignores incremental and rebuilds all from START_DATE
    """
    out_dir = fileloc.bacen_downloaded_data_folder
    os.makedirs(out_dir, exist_ok=True)

    raw_path = os.path.join(out_dir, "bcb_dashboard_raw.csv")
    monthly_path = os.path.join(out_dir, "bcb_dashboard_monthly.csv")
    ready_path = os.path.join(out_dir, "bcb_dashboard_ready.csv")
    ready_trading_path = os.path.join(out_dir, "bcb_dashboard_ready_trading.csv")

    # Load existing if present (to support incremental)
    existing_df = None
    last_date_global = None
    if os.path.exists(raw_path) and not force_full_refresh:
        try:
            existing_df = pd.read_csv(raw_path, index_col="date", parse_dates=True)
            if not existing_df.empty:
                last_date_global = existing_df.index.max().date()
        except Exception:
            existing_df = None
            last_date_global = None

    if debug:
        print(f"\n=== build_bcb_files ===")
        print(f"OUT_DIR = {out_dir}")
        print(f"Existing last date = {last_date_global}")
        if force_full_refresh:
            print("FORCE full refresh enabled: rebuilding from START_DATE")

    all_series = {}

    for sgs_code, meta in BCB_SGS_SERIES.items():
        full_name = meta.get("full_name") 
        short_name = meta.get("short_name")
        periodicity = meta.get("periodicity", "M")  # default monthly if not specified

        # decide dynamic start depending on incremental and periodicity
        if force_full_refresh or last_date_global is None:
            dynamic_start = START_DATE
        else:
            # safe dynamic start: use last_date_global or a frequency-aware start
            if periodicity == "D":
                dynamic_start = last_date_global + timedelta(days=1)
            elif periodicity == "M":
                # start of current month to fetch possible new monthly obs
                today = date.today()
                dynamic_start = date(today.year, today.month, 1)
            elif periodicity == "Q":
                today = date.today()
                q_start_month = ((today.month - 1) // 3) * 3 + 1
                dynamic_start = date(today.year, q_start_month, 1)
            else:
                dynamic_start = last_date_global + timedelta(days=1)

                # ------------------------------------------------------
        # Dynamic start logic (FINAL FIX)
        # ------------------------------------------------------
        if force_full_refresh or last_date_global is None:
            dynamic_start = START_DATE
        else:
            # Normal series: update only the current period
            if periodicity == "D":
                # DAILY series: ALWAYS start from last_date_global
                # Never from today, never skip
                dynamic_start = last_date_global + timedelta(days=1)
            elif periodicity == "M":
                today = date.today()
                dynamic_start = date(today.year, today.month, 1)
            elif periodicity == "Q":
                today = date.today()
                q_start = ((today.month - 1) // 3) * 3 + 1
                dynamic_start = date(today.year, q_start, 1)
            else:
                dynamic_start = last_date_global + timedelta(days=1)

        # ------------------------------------------------------
        # ABSOLUTE RULE: NEVER SKIP SELIC (11 and 1178)
        # ------------------------------------------------------
        if periodicity == "D":
            dynamic_start = last_date_global or START_DATE
        else:
            # For all other series keep the normal skip logic
            if dynamic_start > END_DATE:
                if debug:
                    print(f"  Skipping {sgs_code} ({short_name}): dynamic start > END_DATE")
                continue

        # fetch
        try:
            s_new = fetch_series(sgs_code, start=dynamic_start, end=END_DATE, max_years=DEFAULT_MAX_YEARS_PER_REQUEST, debug=debug)
        except Exception as e:
            print(f"  Exception while fetching {sgs_code}: {e}")
            s_new = pd.Series(dtype="float64", name=full_name)

        # rename series to human-friendly full_name for merging
        if s_new is not None and not s_new.empty:
            s_new.name = full_name
        else:
            s_new = pd.Series(dtype="float64", name=full_name)

        # merge with existing
        if existing_df is not None and full_name in existing_df.columns:
            s_old = existing_df[full_name]
            if s_new.empty:
                s_merged = s_old
            else:
                s_merged = pd.concat([s_old, s_new]).sort_index().drop_duplicates()
        else:
            s_merged = s_new

        all_series[full_name] = s_merged
        if debug:
            print(f"  -> SGS {sgs_code}-{short_name}' merged length = {len(s_merged)} (last index = {s_merged.index.max() if len(s_merged)>0 else 'N/A'})")

    # Combine into dataframe
    if not all_series:
        print("No series produced. Exiting.")
        return

    df_raw = pd.concat(all_series.values(), axis=1, join="outer")
    df_raw.columns = list(all_series.keys())
    df_raw.index = pd.to_datetime(df_raw.index)
    df_raw = df_raw.sort_index()
    df_raw = df_raw.dropna(axis=1, how="all")

    if debug:
        print("\nFinal columns:", df_raw.columns.tolist())
        print(f"Saving raw to: {raw_path}")

    df_raw.to_csv(raw_path, index_label="date")

    # Monthly
    df_monthly = df_raw.resample("ME").last()
    df_monthly.to_csv(monthly_path, index_label="date")
    if debug:
        print(f"Saved monthly to: {monthly_path}")

    # READY: forward-fill on calendar days (so daily series have no gaps)
    df_ready = df_raw.sort_index().ffill().dropna(how="all")
    df_ready.to_csv(ready_path, index_label="date")
    if debug:
        print(f"Saved ready (calendar daily, ffilled) to: {ready_path}")

    # READY_TRADING: if we can find an IBOV trading calendar, reindex to it
    try:
        ibov_index_path = os.path.join(fileloc.yahoo_downloaded_data_folder, "INDEX_^BVSP.csv")
        if os.path.exists(ibov_index_path):
            df_ibov = pd.read_csv(ibov_index_path, parse_dates=["Date"], index_col="Date")
            trading_index = df_ibov.index.sort_values()
            df_ready_trading = df_ready.reindex(trading_index).ffill().dropna(how="all")
            df_ready_trading.to_csv(ready_trading_path, index_label="date")
            if debug:
                print(f"Saved ready (reindexed to trading BVSP dates) to: {ready_trading_path}")
        else:
            if debug:
                print(f"IBOV index file not found at: {ibov_index_path}. Skipping ready_trading generation.")
    except Exception as e:
        print(f"Error while creating ready_trading file: {e}")

    if debug:
        print("build_bcb_files completed.")
