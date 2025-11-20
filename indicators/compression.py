import pandas as pd
from core.constants import mas_list, ma_groups
from core.types import CompressionResult


def calculate_compression(data, ma_result):
    df_idx = ma_result.idx.copy()
    df_eod = ma_result.eod.copy()


    close = df_eod['Adj Close']


    for ma in mas_list:
        dif = (close - df_eod[f'MA{ma}']) / close
        df_idx[f'Abs_C-MA{ma}'] = dif.abs().sum(axis=1)
        df_idx[f'Dir_C-MA{ma}'] = dif.sum(axis=1)


    return CompressionResult(idx=df_idx, eod=df_eod)