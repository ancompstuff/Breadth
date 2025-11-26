import pandas as pd
from core.constants import mas_list
from core.my_data_types import BreadthResult


def calculate_breadth(data, ma_result):
    df_idx = ma_result.idx.copy()
    df_eod = ma_result.eod.copy()

    close = df_eod['Adj Close']

    frames = []
    for ma in mas_list:
        ma_values = df_eod[f'MA{ma}']
        comp = (close > ma_values).astype(int) - (close < ma_values).astype(int)
        frames.append(comp)


    df = pd.concat(frames, axis=1)
    return BreadthResult(df=df)