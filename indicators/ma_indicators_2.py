import pandas as pd
from core.constants import trend_combinations


def build_vwma_trend_counts_and_percents(
    df_eod_with_mas_vwmas: pd.DataFrame,
    combinations: dict[str, list[str]] = trend_combinations
) -> pd.DataFrame:
    """
    Builds Nº>VWMA... and %>VWMA... trend series from EOD data.

    Assumes:
        columns MultiIndex
        level 0 = field  (Adj Close, VWMA5, VWMA12, ...)
        level 1 = ticker

    Parameters
    ----------
    df_eod_with_mas_vwmas : pd.DataFrame
        EOD dataframe with Adj Close and VWMA fields.

    combinations : dict
        Mapping label -> list of VWMA fields
        e.g. {"VWMA5&12": ["VWMA5", "VWMA12"], ...}

    Returns
    -------
    pd.DataFrame
        Columns:
            Nº>VWMA...
            %>VWMA...
    """

    # --- structural sanity check ---
    assert "Adj Close" in df_eod_with_mas_vwmas.columns.levels[0]

    # --- base data ---
    adj = df_eod_with_mas_vwmas.xs("Adj Close", level=0, axis=1)
    n_tickers = adj.shape[1]

    out = {}

    for label, vwmas in combinations.items():

        # initialize with first VWMA condition
        vwma_df = df_eod_with_mas_vwmas.xs(vwmas[0], level=0, axis=1)
        cond = adj > vwma_df

        # AND remaining conditions
        for vwma in vwmas[1:]:
            vwma_df = df_eod_with_mas_vwmas.xs(vwma, level=0, axis=1)
            cond &= adj > vwma_df

        count_col = f"Nº>{label}"
        pct_col   = f"%>{label}"

        counts = cond.sum(axis=1)

        out[count_col] = counts
        out[pct_col]   = counts / n_tickers * 100.0

    return pd.DataFrame(out, index=df_eod_with_mas_vwmas.index)
