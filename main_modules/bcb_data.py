# bcb_data.py
import os
import requests
import pandas as pd

# BCB series codes: IPCA=433, SELIC=4390 by default
DEFAULT_SERIES_MAP = {433: "IPCA", 4390: "SELIC"}

def _get_bcb_series(series_code, start_date, end_date):
    """
    Returns a DataFrame indexed by date with a single column named str(series_code).
    start_date / end_date should be 'dd/mm/YYYY' (same as your bacen test.py).
    """
    BASE_URL = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados?"
        "formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )
    url = BASE_URL.format(series_code=series_code, start_date=start_date, end_date=end_date)
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df = df.set_index('data')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df = df.rename(columns={'valor': str(series_code)})
        return df[[str(series_code)]]
    except Exception as e:
        print(f"Error fetching BCB series {series_code}: {e}")
        return None


def fetch_and_merge_bcb(series_map=None, start_date='01/01/2000', end_date='31/12/2099'):
    """
    Fetch multiple series from BCB and merge to a single DataFrame indexed by date.
    series_map: dict mapping code -> name (e.g. {433:'IPCA', 4390:'SELIC'}) or None use DEFAULT_SERIES_MAP
    start_date / end_date format: dd/mm/YYYY
    """
    series_map = series_map or DEFAULT_SERIES_MAP
    merged = None
    for code, display in series_map.items():
        df = _get_bcb_series(code, start_date, end_date)
        if df is None:
            print(f"Warning: no data for BCB series {code}")
            continue
        df = df.rename(columns={str(code): display})
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, left_index=True, right_index=True, how='outer')
    return merged


def download_and_save_bcb(fileloc_downloaded_data_folder, start_date, end_date, series_map=None, filename="BCB_IPCA_SELIC.csv"):
    """
    Fetches BCB series and writes CSV to <downloaded_data_folder>/bcb/<filename>.
    start_date / end_date must be 'dd/mm/YYYY'.
    Returns full path or None on failure.
    """
    out_dir = os.path.join(fileloc_downloaded_data_folder, "bcb")
    os.makedirs(out_dir, exist_ok=True)
    df = fetch_and_merge_bcb(series_map=series_map, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        print("No BCB data downloaded.")
        return None
    out_path = os.path.join(out_dir, filename)
    df.to_csv(out_path)
    print(f"Saved BCB series to {out_path}")
    return out_path



"""def download_bcb(start_date, end_date, fileloc, config):
    series_map = {
        config.ipca_code: "IPCA",
        config.selic_code: "SELIC"
    }
    df = fetch_and_merge_bcb(series_map, start_date, end_date)
    if df is None:
        print("BCB returned no data.")
        return
    path = os.path.join(fileloc.bcb_data_folder, "BCB_IPCA_SELIC.csv")
    df.to_csv(path)
    print(f"BCB data saved: {path}")"""