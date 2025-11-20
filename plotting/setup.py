from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class PlotSetup:
    idx: str
    mkt: str
    df_to_plot: pd.DataFrame
    lookback: int
    num_tickers: int
    ymin: float
    ymax: float
    date_labels: list
    tick_positions: list


    def apply_xaxis(self, ax):
        ax.set_xticks(self.tick_positions)
        ax.set_xticklabels(self.date_labels, rotation=45, fontsize=8)