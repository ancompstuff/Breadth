from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class Config:
    """
    Runtime configuration for the analysis session.
    This is populated during setup (user choices + system defaults).
    """
    to_do: int
    market_to_study: dict
    number_tickers: int
    to_update: dict | None
    graph_lookback: int
    first_date_to_download: str
    last_date_to_download: str
    yahoo_end_date: str
    study_end_date: str

    def to_dict(self):
        """
        Convert the Config dataclass into a regular dictionary.

        JSON cannot serialize custom classes (like Config), but it can serialize
        basic Python types such as dicts, lists, strings, and numbers. This method
        provides a JSON-friendly representation of the configuration so it can be
        saved to config.json or printed with json.dumps().
        """
        return asdict(self)


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

