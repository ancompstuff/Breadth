# plotting/plot_bcb.py
import matplotlib.pyplot as plt

def _plot_ibov_price_layer(ax, dates, series_ibov, plot_setup=None):
    """
    Draw IBOV as black line + grey filled area between min and series.
    If plot_setup is provided and has method plot_price_layer(ax, ...),
    the function will try to delegate to it (best-effort).
    """
    # If the user provided a PlotSetup-like object that contains a helper, prefer it.
    if plot_setup is not None and hasattr(plot_setup, "plot_price_layer"):
        try:
            # try a best-effort call signature - many PlotSetup variants exist.
            plot_setup.plot_price_layer(ax=ax, dates=dates, series=series_ibov)
            return
        except Exception:
            # fallback to manual drawing
            pass

    # Manual fallback drawing:
    min_val = series_ibov.min()
    max_val = series_ibov.max()
    ax.plot(dates, series_ibov, color='black', linewidth=1)
    ax.fill_between(dates, min_val, series_ibov, color='lightgrey', alpha=0.85)
    ax.set_ylabel('^BVSP', color='black')
    ax.tick_params(axis='y', labelcolor='black')
    ax.set_ylim(min_val, max_val)


def plot_selic_vs_ibov(ax, df_selic_vs_ibov, plot_setup=None):
    """
    ax: axes for IBOV (left)
    df_selic_vs_ibov: DataFrame with index dates and columns ['IBOV','SELIC']
    plot_setup: optional PlotSetup object (used only to draw the IBOV price layer if present)
    """
    if df_selic_vs_ibov is None or df_selic_vs_ibov.empty:
        ax.text(0.5, 0.5, "SELIC data not available", ha='center', va='center')
        ax.set_title('SELIC vs ^BVSP')
        return

    dates = df_selic_vs_ibov.index
    ibov = df_selic_vs_ibov['IBOV']
    selic = df_selic_vs_ibov['SELIC']

    # Left axis: IBOV (price layer)
    _plot_ibov_price_layer(ax, dates, ibov, plot_setup=plot_setup)
    ax.set_title('SELIC vs ^BVSP')

    # Right twin axis: SELIC linear line
    ax2 = ax.twinx()
    ax2.plot(dates, selic, linewidth=1.2, label='SELIC')
    ax2.set_ylabel('SELIC (monthly, forward-filled)', color='tab:blue')
    ax2.tick_params(axis='y', labelcolor='tab:blue')


def plot_ipca_vs_ibov(ax, df_ipca_vs_ibov, plot_setup=None):
    """
    ax: axes for IBOV (left)
    df_ipca_vs_ibov: DataFrame with index dates and columns ['IBOV','IPCA']
    """
    if df_ipca_vs_ibov is None or df_ipca_vs_ibov.empty:
        ax.text(0.5, 0.5, "IPCA data not available", ha='center', va='center')
        ax.set_title('IPCA vs ^BVSP')
        return

    dates = df_ipca_vs_ibov.index
    ibov = df_ipca_vs_ibov['IBOV']
    ipca = df_ipca_vs_ibov['IPCA']

    # Left axis: IBOV (price layer)
    _plot_ibov_price_layer(ax, dates, ibov, plot_setup=plot_setup)
    ax.set_title('IPCA vs ^BVSP')

    # Right twin axis: IPCA linear line
    ax2 = ax.twinx()
    ax2.plot(dates, ipca, linewidth=1.2, label='IPCA')
    ax2.set_ylabel('IPCA (monthly, forward-filled)', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
