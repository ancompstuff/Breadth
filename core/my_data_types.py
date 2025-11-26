from dataclasses import dataclass, asdict
import pandas as pd
import json, os
from pathlib import Path


#==========================================================================================
# FileLocations
#==========================================================================================
@dataclass
class FileLocations:
    downloaded_data_folder: str
    pdf_folder: str
    codes_to_download_folder: str

def load_file_locations(path: Path = None) -> FileLocations:
    """
    Load file_locations.json into FileLocations dataclass.
    - If no path is given, look for file_locations.json in the same directory as this file (core).
    - If a path is given, resolve it absolutely.
    - All folder paths inside the JSON are resolved absolutely relative to the JSON file's location.
    """
    if path is None:
        # Use config relative to this source file location
        here = Path(__file__).resolve().parent
        json_path = here / "file_locations.json"
    else:
        json_path = Path(path).resolve()  # absolute path to JSON config

    if not json_path.exists():
        raise FileNotFoundError(f"file_locations.json not found at {json_path}")

    # Load JSON data
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Base path for relative folder paths inside JSON file
    base = json_path.parent

    def resolve_folder(p: str) -> str:
        """Resolve folder path absolutely relative to JSON location."""
        if not p:
            return p
        return str((base / p).resolve())

    return FileLocations(
        downloaded_data_folder=resolve_folder(data["downloaded_data_folder"]),
        pdf_folder=resolve_folder(data["pdf_folder"]),
        codes_to_download_folder=resolve_folder(data["codes_to_download_folder"]),
    )


#==========================================================================================
# Config
#==========================================================================================
@dataclass
class Config:
    """
    Container for all runtime parameters used by the analysis pipeline.

    This object is created once during user setup and then passed through
    the rest of the system to control:

    """
    to_do: int  # what operations to perform
    market_to_study: dict  # key: int (1-5) value: dict (market, idx_code, codes_csv, number_tickers)
    to_update: dict | None  # same idea as market_to_study, but might be all of them
    graph_lookback: int  # lookback window length for charts
    yf_start_date: str  # begin download date, only used for starting fresh databases
    download_end_date: str  # last date you want included in the download
    yf_end_date: str  # last_date_to_download +1 because yFinance doesn't include the last date
    study_end_date: str  # used when using custom studies or test

    def to_dict(self):
        """
        Convert the dataclass into a pure-Python dictionary suitable for JSON dumping.

        NumPy numerical types (np.int*, np.float*) often appear inside DataFrames or
        metadata dictionaries. JSON cannot serialize NumPy scalars directly, so this
        helper walks every value in the structure and converts NumPy types to the
        closest built-in Python type (int or float). Structures are processed
        recursively to ensure there are no serialization failures.

        Returns
        -------
        dict
            A fully native Python dictionary with no NumPy scalars.
        """
        import numpy as np
        
        def convert(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                return float(obj)
            elif isinstance(obj, (list, tuple)):
                return [convert(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj
            
        result = asdict(self)
        return convert(result)


#==========================================================================================
# Other Dataclasses
#==========================================================================================
@dataclass
class MarketData:
    idx: pd.DataFrame
    comp: pd.DataFrame
    config: Config


@dataclass
class MAResult:
    idx: pd.DataFrame
    comp: pd.DataFrame


@dataclass
class BreadthResult:
    df: pd.DataFrame


@dataclass
class CompressionResult:
    idx: pd.DataFrame
    comp: pd.DataFrame

