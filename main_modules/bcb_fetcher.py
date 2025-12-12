"""
bcb_fetcher.py

Low-level JSON-only BCB fetcher with chunking and robust cleaning.
Debug-friendly: prints status for each chunk/series.

Public function:
    fetch_series(sgs_code: int, start: date, end: date) -> pd.Series
"""
import requests
import pandas as pd
from datetime import date, timedelta
from typing import Optional
import math
import re

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

# maximum years allowed per request according to BCB CSV/JSON rules (safe)
MAX_YEARS_DEFAULT = 10

# Legacy/fragile series that historically need special handling
LEGACY_JSON_ALWAYS = {11, 1178}

# helper: split into <= max_years chunks
def _generate_chunks(start: date, end: date, max_years: int = MAX_YEARS_DEFAULT):
    cur = start
    while cur <= end:
        year_limit = cur.year + max_years - 1
        chunk_end = date(year_limit, 12, 31)
        if chunk_end > end:
            chunk_end = end
        yield cur, chunk_end
        cur = date(chunk_end.year + 1, 1, 1)

def _date_to_str(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def _clean_val_str_to_float(v) -> Optional[float]:
    """Robustly extract a float from weird strings like '0      050788' or '"0,050788"'."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    # remove quotes and spaces
    s = s.replace('"', "").replace(" ", "")
    # convert comma decimal to dot
    s = s.replace(",", ".")
    # keep only first numeric match
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None

def _df_from_json_list(data_json):
    """Convert JSON list returned by BCB into dataframe with lower-case columns."""
    if not data_json:
        return pd.DataFrame(columns=["data", "valor"])
    df = pd.DataFrame(data_json)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def fetch_series(
    sgs_code: int,
    start: date,
    end: date,
    max_years: int = MAX_YEARS_DEFAULT,
    debug: bool = True,
) -> pd.Series:
    """
    Fetch an SGS series using JSON (preferred) in chunked requests.
    Returns a pd.Series indexed by datetime (date) with float values.
    Series name will be the numeric sgs_code as string; caller may rename.

    - Uses JSON for all requests (robust).
    - For legacy series (11,1178) does extra cleaning and converts 0->NaN (holidays).
    - Respects max_years per chunk.
    """
    if debug:
        print(f"[bcb_fetcher] fetch_series() sgs_code={sgs_code} start={start} end={end}")

    chunks = list(_generate_chunks(start, end, max_years=max_years))
    all_dfs = []

    headers = {"User-Agent": "python-requests-bcb-fetcher/1.0", "Accept": "application/json"}

    for cs, ce in chunks:
        params = {"formato": "json", "dataInicial": _date_to_str(cs), "dataFinal": _date_to_str(ce)}
        url = BASE_URL.format(code=sgs_code)
        if debug:
            print(f"  -> chunk {cs} to {ce} (params: {params})")
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            r.raise_for_status()
        except requests.HTTPError as e:
            print(f"    HTTP error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue
        except requests.RequestException as e:
            print(f"    Request error for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue

        # parse JSON
        try:
            data_json = r.json()
        except Exception as e:
            print(f"    Failed to parse JSON for sgs_code {sgs_code} on {params['dataInicial']}–{params['dataFinal']}: {e}")
            continue

        df = _df_from_json_list(data_json)

        # require expected columns
        if "data" not in df.columns or "valor" not in df.columns:
            print(f"    Unexpected JSON columns for sgs_code {sgs_code}: {df.columns.tolist()} — skipping chunk.")
            continue

        # parse dates
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

        # clean numeric values robustly
        if sgs_code in LEGACY_JSON_ALWAYS:
            df["valor"] = df["valor"].apply(_clean_val_str_to_float)
        else:
            # sometimes valor is numeric or string with comma
            def _safe_numeric(x):
                if x is None:
                    return None
                if isinstance(x, (int, float)) and (not (isinstance(x, float) and math.isnan(x))):
                    return float(x)
                return _clean_val_str_to_float(x)
            df["valor"] = df["valor"].apply(_safe_numeric)

        # convert to numeric dtype (NaN where invalid)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

        # Known behavior: some daily series use 0 as placeholder on holidays → treat as missing
        if sgs_code in LEGACY_JSON_ALWAYS:
            # convert exact zeros to NaN
            df.loc[df["valor"] == 0, "valor"] = pd.NA

        all_dfs.append(df[["data", "valor"]])

    if not all_dfs:
        if debug:
            print(f"  !! No valid data fetched for sgs_code {sgs_code}. Returning empty series.")
        return pd.Series(dtype="float64", name=str(sgs_code))

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["data"]).sort_values("data")

    series = combined.set_index("data")["valor"].astype("float64")
    series.name = str(sgs_code)

    # Forward-fill only for legacy daily series (to fill holidays)
    if sgs_code in LEGACY_JSON_ALWAYS:
        if debug:
            print(f"  -> forward-filling legacy daily series {sgs_code}")
        series = series.ffill()

    if debug:
        print(f"  -> fetched {len(series)} observations for sgs_code {sgs_code} (from {series.index.min()} to {series.index.max()})")

    return series
