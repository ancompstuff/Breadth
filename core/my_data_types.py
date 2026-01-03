from dataclasses import dataclass, asdict, field
import matplotlib.pyplot as plt
import pandas as pd
from contextlib import contextmanager
import time


#==========================================================================================
# FileLocations
#==========================================================================================
@dataclass
class FileLocations:
    yahoo_downloaded_data_folder: str
    bacen_downloaded_data_folder: str
    pdf_folder: str
    codes_to_download_folder: str

def load_file_locations_dict(d: dict) -> FileLocations:

    """
    Load file_locations dict from core.constants into FileLocations dataclass.
    """

    return FileLocations(
        yahoo_downloaded_data_folder=d["yahoo_downloaded_data_folder"],
        bacen_downloaded_data_folder=d["bacen_downloaded_data_folder"],
        pdf_folder=d["pdf_folder"],
        codes_to_download_folder=d["codes_to_download_folder"],
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
    to_update: dict | None  # Dictionary of one or all dictionaries in the same format as market_to_study
    graph_lookback: int  # lookback window length for charts
    yf_start_date: str  # begin download date, only used for starting fresh databases
    download_end_date: str  # last date you want included in the download
    yf_end_date: str  # last_date_to_download +1 because yFinance doesn't include the last date
    study_end_date: str  # used when using custom studies or test
    #bcb_series: dict = field(default_factory=lambda: {
    #    "ipca": 433,
    #    "selic": 4390
    #})  # Using field, each new Config() gets its own fresh dictionary. Not important in this case. Could hard-code.

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
# Plotting
#==========================================================================================
# Dataclass to reduce repetitive plotting code
@dataclass
class PlotSetup:
    """Container for all common plotting parameters."""
    idx: str
    mkt: str
    price_data: pd.DataFrame  # datetime indexed
    plot_index: pd.Index  # numeric index for plotting: Range Index (0..N)
    lookback_period: int
    num_tickers: int
    sample_start: str
    sample_end: str
    ymin: float
    ymax: float
    date_labels: list[str]
    tick_positions: list[int]

    def apply_xaxis(self, ax: plt.Axes):
        """
        Apply common x-axis formatting (ticks, labels, rotation)
        to the provided Matplotlib axis.
        """
        ax.set_xticks(self.tick_positions)
        ax.set_xticklabels(
            [self.date_labels[i] for i in self.tick_positions],
            rotation=45, fontsize=8
        )

    def plot_price_layer(self, ax):
        """Standard price plotting: black line + grey fill + y-limits."""
        # FIX: Use proper column access for datetime-indexed DataFrame
        # adj = self.price_data.loc[:, "Adj Close"]
        # or simpler:
        adj = self.price_data['Adj Close'].values  # Extract as numpy array directly
        ax.plot(self.plot_index, adj, color="black", linewidth=1.5, zorder=4, label="Preço")
        ax.fill_between(self.plot_index, adj, color="lightgrey")
        ax.set_ylim(self.ymin, self.ymax)
        ax.set_ylabel('Preço', color='black')
        ax.tick_params(axis='y', labelsize=8)
        # VERTICAL GRID (x-axis)
        ax.grid(True, axis='x', linestyle='-', alpha=0.3, color='gray', linewidth=0.8)

    def fix_xlimits(self, ax):
        ax.set_xlim(-0.5, len(self.plot_index) - 0.5)


@contextmanager
def timed_block(name: str):
    start = time.perf_counter()
    print(f"[START] {name}")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[END]   {name} — {elapsed:.3f}s")


from dataclasses import dataclass, asdict, field
import matplotlib.pyplot as plt
import pandas as pd
from contextlib import contextmanager
import time

# ... existing code ...


# =============================================================================
# Breakout indicator condition schema
# =============================================================================
@dataclass(frozen=True, slots=True)
class BreakoutCondition:
    """
    One breakout/breakdown rule definition.

    Attributes
    ----------
    plot_group:
        Used to group conditions for different plots / totals.
        Example: 1 = short-term cluster (1–8 days)
    period_days:
        pct_change lookback in trading days.
    pct:
        Threshold as a decimal (0.04 = 4%).
    up_col / down_col:
        Output column names that will be created in df_idx (aggregates)
        and in df_eod (per ticker, MultiIndex level 0).
    color:
        Plot color used in stacked bars.

    frozen=True makes it immutable (good for constants).
    slots=True reduces memory/overhead (nice but optional).
    """
    plot_group: int
    period_days: int
    pct: float
    up_col: str
    down_col: str
    color: str


#==========================================================================================
# Other Dataclasses
#==========================================================================================

