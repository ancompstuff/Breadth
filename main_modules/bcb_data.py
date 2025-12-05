import requests
import pandas as pd
from pathlib import Path
from core.constants import bcb_series_catalog, bcb_default_series
import time

# --------------------------
# Low-level fetch
# --------------------------

def _get_bcb_series(series_code, start_date, end_date):
    """
    Fetch a single SGS series.
    Returns a DataFrame indexed by date with a single column 'code' (string).
    Dates: 'dd/mm/YYYY'.
    """
    BASE_URL = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados?"
        "formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )
    url = BASE_URL.format(series_code=series_code, start_date=start_date, end_date=end_date)
    name = bcb_series_catalog.get(series_code, f"Series_{series_code}")
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data:
            print(f"⚠️  No data for {name} (code {series_code})")
            return None
        df = pd.DataFrame(data)
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df = df.set_index("data")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        # BCB can use 0 as “no data” for some series – turn to NaN so we don't distort plots
        df["valor"] = df["valor"].replace(0, pd.NA)
        df = df.rename(columns={"valor": str(series_code)})
        return df[[str(series_code)]]
    except Exception as e:
        print(f"❌ Error fetching {name} (code {series_code}): {e}")
        return None


def fetch_and_merge_bcb(series_map=None, start_date="01/01/2000", end_date="31/12/2099"):
    """
    Fetch multiple SGS series and merge into a single DataFrame indexed by date.
    series_map: dict {code:int -> display_name:str}, default = bcb_default_series.
    Dates: 'dd/mm/YYYY'.
    """
    series_map = series_map or bcb_default_series
    merged = None

    print(f"\n📊 Fetching {len(series_map)} BCB series from {start_date} to {end_date}...")

    t0 = time.time()  # start timer

    for code, display in series_map.items():
        df = _get_bcb_series(code, start_date, end_date)
        if df is None:
            print(f"⚠️  Skipping series {display} (code {code})")
            continue
        df = df.rename(columns={str(code): display})
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, left_index=True, right_index=True, how="outer")

    elapsed = time.time() - t0  # seconds

    if merged is not None:
        print(f"✅ BCB merged DataFrame: {len(merged)} rows, columns={list(merged.columns)}"
              f"({elapsed/60:.2f} minutes).")
    else:
        print("❌ No BCB series successfully fetched (duration {elapsed:.2f} seconds)")
    return merged


# --------------------------
# High-level “create / update” functions
# --------------------------

def _to_ddmmyyyy(s: str) -> str:
    """Convert 'YYYY-mm-dd' → 'dd/mm/YYYY' if needed."""
    if "/" in s:
        return s
    yyyy, mm, dd = s.split("-")
    return f"{dd}/{mm}/{yyyy}"


def create_or_update_bcb_database(
    fileloc_bacen_downloaded_data_folder,
    yf_start_date: str,
    yf_end_date: str,
    series_map=None,
    filename: str = "BCB_IPCA_SELIC.csv",
    use_subfolder: bool = False,
):
    """
    Create or fully refresh the BCB “database” CSV.

    Uses the SAME date window (start/end) as Yahoo modules:
      - yf_start_date, yf_end_date in 'YYYY-mm-dd' (same as Config)

    This function:
      - Converts dates to dd/mm/YYYY for BCB
      - Downloads all selected SGS series
      - Saves them to one CSV in bacen_downloaded_data_folder (optionally /bcb)
    """
    base = Path(fileloc_bacen_downloaded_data_folder)
    if base.suffix.lower() == ".csv":
        base = base.parent

    out_dir = base / "bcb" if use_subfolder else base
    out_dir.mkdir(parents=True, exist_ok=True)

    start_bcb = _to_ddmmyyyy(yf_start_date)
    end_bcb = _to_ddmmyyyy(yf_end_date)

    df = fetch_and_merge_bcb(series_map=series_map, start_date=start_bcb, end_date=end_bcb)
    if df is None or df.empty:
        print("❌ No BCB data downloaded.")
        return None

    out_path = out_dir / filename
    df.to_csv(out_path)
    print(f"✅ Saved BCB data to: {out_path}")
    return str(out_path)