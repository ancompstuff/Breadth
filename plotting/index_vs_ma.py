import matplotlib.pyplot as plt
from core.constants import mas_list, ma_color_map


def plot_index_vs_ma(ma_df, setup):
    df = ma_df.tail(setup.lookback)
    fig, ax = plt.subplots(figsize=(18, 7))

    ax.plot(df.index, df['Adj Close'], color='black')
    for ma in mas_list:
        ax.plot(df.index, df[f'MA{ma}'], color=ma_color_map.get(f'MA{ma}', 'grey'))

        setup.apply_xaxis(ax)

    return fig