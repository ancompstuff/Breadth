import requests
import pandas as pd
from datetime import date, timedelta
from io import StringIO
import os

from core.constants import file_locations
from core.my_data_types import load_file_locations_dict
from core.bcb_config import BCB_SERIES, BCB_LONG_BY_CODE


# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

START_DATE = date(2010, 1, 1)
END_DATE = date.today()

DEFAULT_MAX_YEARS_PER_REQUEST = 10
SERIES_MAX_YEARS = {
    1: 5,  # FX – shorter chunks to avoid 504
}


# -----------------------------
# Date helpers
# -----------------------------
def date_to_str(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def generate_date_chunks(start: date, end: date, max_years: int):
    current_start = start
    while current_start <= end:
        year_limit = current_start.year + max_years - 1
        chunk_end = date(year_limit, 12, 31)
        if chunk_end > end:
            chunk_end = end
        yield current_start, chunk_end
        current_start = date(chunk_end.year + 1, 1, 1)


# -----------------------------
# Fetch one BCB_SERIES
# -----------------------------
def fetch_sgs_series(sgs_code: int,
                     start: date = START_DATE,
                     end: date = END_DATE) -> pd.Series:
    max_years = SERIES_MAX_YEARS.get(sgs_code, DEFAULT_MAX_YEARS_PER_REQUEST)
    all_chunks = []

    for chunk_start, chunk_end in generate_date_chunks(start, end, max_years):
        params = {
            "formato": "csv",
            "dataInicial": date_to_str(chunk_start),
            "dataFinal": date_to_str(chunk_end),
        }
        url = BASE_URL.format(code=sgs_code)
        headers = {
            "User-Agent": "python-requests-bcb-dashboard/1.0",
            "Accept": "text/csv, */*;q=0.8",
        }
        print(f"  -> chunk {date_to_str(chunk_start)} to {date_to_str(chunk_end)}")
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.HTTPError as e:
            print(f"    HTTP error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue
        except requests.RequestException as e:
            print(f"    Request error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue

        text = resp.text
        if not text.strip():
            print(f"    Empty response for sgs_code {sgs_code} on this chunk; skipping.")
            continue

        first_100 = text[:100].lower()
        if "<html" in first_100 or "<!doctype html" in first_100:
            print(f"    Non-CSV (HTML) response for sgs_code {sgs_code}; skipping this chunk.")
            continue

        try:
            df = pd.read_csv(
                StringIO(text),
                sep=";",
                decimal=",",
                parse_dates=["data"],
                dayfirst=True,
            )
        except ValueError as e:
            print(f"    CSV parse error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            try:
                df_raw = pd.read_csv(StringIO(text), sep=";", decimal=",")
                print(f"    Raw columns for sgs_code {sgs_code}: {df_raw.columns.tolist()}")
            except Exception as e2:
                print(f"    Failed to inspect raw CSV for sgs_code {sgs_code}: {e2}")
            continue
        except Exception as e:
            print(f"    Unexpected CSV error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue

        df.columns = [c.strip().lower() for c in df.columns]
        if "data" not in df.columns or "valor" not in df.columns:
            print(f"    Unexpected CSV columns for sgs_code {sgs_code}: {df.columns.tolist()} – skipping chunk.")
            continue

        all_chunks.append(df[["data", "valor"]])

    if not all_chunks:
        print(f"  !! No valid data fetched for sgs_code {sgs_code}.")
        return pd.Series(dtype="float64")

    full_df = pd.concat(all_chunks, ignore_index=True)

    full_df = pd.concat(all_chunks, ignore_index=True)
    full_df = full_df.drop_duplicates(subset=["data"]).sort_values("data")

    s = full_df.set_index("data")["valor"].astype("float64")
    s.name = BCB_LONG_BY_CODE.get(sgs_code, str(sgs_code))
    return s


# -----------------------------
# MAIN FUNCTION: build_bcb_files
# -----------------------------
def build_bcb_files(fileloc):
    """
    Download BCB data and write:
      - bcb_dashboard_raw.csv
      - bcb_dashboard_monthly.csv
      - BCB_IPCA_SELIC.csv (Selic Diária + IPCA subset)
    into fileloc.bacen_downloaded_data_folder.
    """

    ##################################################################################################
    # For one-time full refresh, force downloader to ignore last_date_global and reload all from 2010:
    # run in terminal:
    #

    # Use correct dynamic start date block below
    ##################################################################################################

    OUT_DIR = fileloc.bacen_downloaded_data_folder
    os.makedirs(OUT_DIR, exist_ok=True)

    raw_csv_path = os.path.join(OUT_DIR, "bcb_dashboard_raw.csv")

    # ------------------------------------
    # 0) Load existing raw data if present
    # ------------------------------------
    existing_df = None
    last_date_global = None

    if os.path.exists(raw_csv_path):
        existing_df = pd.read_csv(raw_csv_path, index_col="date", parse_dates=True)
        if not existing_df.empty:
            last_date_global = existing_df.index.max().date()

    ########################################
    # Decide dynamic START_DATE for this run
    # NORMAL USE
    ########################################
    if last_date_global is not None:
        dynamic_start = last_date_global + timedelta(days=1)
    else:
        dynamic_start = START_DATE

    """########################################
    # Decide dynamic START_DATE for this run
    # USE WHEN DOING REFRESH
    ########################################
    if last_date_global is not None:
        # TEMPORARY: force full rebuild
        # dynamic_start = last_date_global + timedelta(days=1)
        dynamic_start = START_DATE
    else:
        dynamic_start = START_DATE"""


    print(f"BCB download start date for this run: {dynamic_start} (end = {END_DATE})")

    # -----------------------------
    # Download all BCB_SERIES
    # -----------------------------
    all_series = {}

    for sgs_code, meta in BCB_SERIES.items():
        long_name = meta["long_name"]
        print(f"Downloading {sgs_code} - {long_name} ...")
        s_new = fetch_sgs_series(sgs_code, start=dynamic_start, end=END_DATE)

        if existing_df is not None and long_name in existing_df.columns:
            # Existing series: merge old + new
            s_old = existing_df[long_name]

            if s_new is None or s_new.empty:
                # Keep the old data; nothing new fetched
                print(f"    No new data for {long_name}; keeping existing series.")
                s_merged = s_old
            else:
                s_merged = (
                    pd.concat([s_old, s_new])
                    .sort_index()
                    .drop_duplicates()
                )
            all_series[long_name] = s_merged

        else:
            # New series: only add if we fetched something
            if s_new is None or s_new.empty:
                print(f"    No data fetched for NEW series {long_name}; skipping (won't add empty column).")
                continue
            else:
                all_series[long_name] = s_new

    # Align into one DataFrame
    df = pd.concat(all_series.values(), axis=1, join="outer")
    df.columns = list(all_series.keys())
    df.index = pd.to_datetime(df.index)
    df = df.dropna(axis=1, how="all")

    print("\nDataFrame index type:", type(df.index))
    print("Columns:", df.columns.tolist())
    print("Head:\n", df.head())

    # Save raw
    df.to_csv(raw_csv_path, index_label="date")
    print(f"Saved raw data to: {raw_csv_path}")

    # Monthly
    df_m = df.resample("ME").last()
    monthly_csv_path = os.path.join(OUT_DIR, "bcb_dashboard_monthly.csv")
    df_m.to_csv(monthly_csv_path, index_label="date")
    print(f"Saved monthly data to: {monthly_csv_path}")

    # Subset for get_idx1_idx2: Selic Diária + IPCA
    subset_cols = [c for c in df_m.columns if c in ["Selic Diária", "IPCA"]]
    bcb_subset = df_m[subset_cols].copy()
    bcb_ipca_selic_path = os.path.join(OUT_DIR, "BCB_IPCA_SELIC.csv")
    bcb_subset.to_csv(bcb_ipca_selic_path, index_label="date")
    print(f"Saved BCB_IPCA_SELIC.csv to: {bcb_ipca_selic_path}")


# -----------------------------
# Standalone execution
# -----------------------------
if __name__ == "__main__":
    fileloc = load_file_locations_dict(file_locations)
    build_bcb_files(fileloc)