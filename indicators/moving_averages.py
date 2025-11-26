import pandas as pd
from core.constants import mas_list
from core.my_data_types import MAResult


def calculate_mas(data):
    df_idx = data.idx.copy()
    df_eod = data.eod.copy()


    # index
    close = df_idx['Adj Close']
    vol = df_idx['Volume']
    for ma in mas_list:
        df_idx[f'MA{ma}'] = close.rolling(ma).mean()
        df_idx[f'VWMA{ma}'] = (close * vol).rolling(ma).sum() / vol.rolling(ma).sum()


    # tickers
    close_eod = df_eod['Adj Close']
    vol_eod = df_eod['Volume']
    for ma in mas_list:
        df_eod[(f'MA{ma}', '')] = close_eod.rolling(ma).mean()
        df_eod[(f'VWMA{ma}', '')] = (close_eod * vol_eod).rolling(ma).sum() / vol_eod.rolling(ma).sum()


    return MAResult(idx=df_idx, eod=df_eod)