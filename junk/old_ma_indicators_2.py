import pandas as pd
from core.constants import mas_list, ma_groups

# =====================================================================
# 1. VWMA BREADTH (%>VWMA, %<VWMA)
# =====================================================================

def build_vwma_trend_counts_and_percents(
    df_eod_with_vwmas: pd.DataFrame,
) -> pd.DataFrame:
    """Build classic VWMA breadth series.

    For each VWMA period p in mas_list, compute per-date counts and percents of
    tickers with price above/below VWMAp.

    Output columns (for each p):
        Nº>V{p}, %>V{p}
        Nº<V{p}, %<V{p}
    """

    assert "Adj Close" in df_eod_with_vwmas.columns.levels[0]

    adj = df_eod_with_vwmas.xs("Adj Close", level=0, axis=1)
    n_tickers = adj.shape[1]

    out: dict[str, pd.Series] = {}

    for p in mas_list:
        vwma = df_eod_with_vwmas.xs(f"VWMA{p}", level=0, axis=1)

        above = adj > vwma
        below = adj < vwma

        out[f"Nº>V{p}"] = above.sum(axis=1)
        out[f"%>V{p}"] = above.sum(axis=1) / n_tickers * 100.0

        out[f"Nº<V{p}"] = below.sum(axis=1)
        out[f"%<V{p}"] = below.sum(axis=1) / n_tickers * 100.0

    return pd.DataFrame(out, index=df_eod_with_vwmas.index)


# =====================================================================
# 2. TRUE LADDER LOGIC (STRICT STRUCTURE)
# =====================================================================

def _strict_ladder_condition(
    adj: pd.DataFrame,
    vwmas: list[pd.DataFrame],
) -> pd.DataFrame:
    """Enforce a strict ladder:

        price > v0 > v1 > v2 > ...

    Returns a boolean DataFrame (date x ticker).
    """

    cond = adj > vwmas[0]

    for prev, curr in zip(vwmas[:-1], vwmas[1:]):
        cond &= prev > curr

    return cond


# =====================================================================
# 3. TRUE VWMA LADDERS (MAIN + SELECTED MINI)
# =====================================================================

def _vwma(df_eod_with_vwmas: pd.DataFrame, p: int) -> pd.DataFrame:
    return df_eod_with_vwmas.xs(f"VWMA{p}", level=0, axis=1)



def build_vwma_true_ladders(
    df_eod_with_vwmas: pd.DataFrame,
) -> pd.DataFrame:
    """Build TRUE VWMA ladders (percent of tickers satisfying strict structure).

    Produces:

    1) MAIN ladder prefixes from VWMA5 -> VWMA200 (using mas_list order):
        $>V5
        $>V5>V12
        ...
        $>V5>...>V200

    2) MINI ladders that DO NOT depend on lower VWMAs:

       - mini$>40 ladder (uses only VWMA40/50/60):
            mini$>V40
            mini$>V40>V50
            mini$>V40>V50>V60

       - mini$>80 ladder (uses only VWMA80/100/200):
            mini$>V80
            mini$>V80>V100
            mini$>V80>V100>V200

    Notes:
    - All outputs are percentages (0..100), not counts.
    - The mini ladders are computed from scratch (price > first VWMA, then strict
      ordering within the mini set). They do not require anything about VWMA < 40
      or < 80.
    """

    assert "Adj Close" in df_eod_with_vwmas.columns.levels[0]

    adj = df_eod_with_vwmas.xs("Adj Close", level=0, axis=1)
    n_tickers = adj.shape[1]

    out: dict[str, pd.Series] = {}

    # ---------------------------------------------------------------
    # 1) MAIN LADDER (mas_list)
    # ---------------------------------------------------------------
    for i in range(len(mas_list)):
        rung = mas_list[: i + 1]

        vwmas = [_vwma(df_eod_with_vwmas, p) for p in rung]

        cond = _strict_ladder_condition(adj, vwmas)
        pct = cond.sum(axis=1) / n_tickers * 100.0

        label = "$>" + ">".join(f"V{p}" for p in rung)
        out[label] = pct

    # ---------------------------------------------------------------
    # 2) MINI LADDER: 40/50/60 (independent of lower VWMAs)
    # ---------------------------------------------------------------
    mini40_periods = ma_groups["medium"]["periods"]
    for i in range(len(mini40_periods)):
        rung = mini40_periods[: i + 1]
        vwmas = [_vwma(df_eod_with_vwmas, p) for p in rung]

        cond = _strict_ladder_condition(adj, vwmas)
        pct = cond.sum(axis=1) / n_tickers * 100.0

        label = "mini$>" + ">".join(f"V{p}" for p in rung)
        out[label] = pct

    # ---------------------------------------------------------------
    # 3) MINI LADDER: 80/100/200 (independent of lower VWMAs)
    # ---------------------------------------------------------------
    mini80_periods = ma_groups["long"]["periods"]
    for i in range(len(mini80_periods)):
        rung = mini80_periods[: i + 1]
        vwmas = [_vwma(df_eod_with_vwmas, p) for p in rung]

        cond = _strict_ladder_condition(adj, vwmas)
        pct = cond.sum(axis=1) / n_tickers * 100.0

        label = "mini$>" + ">".join(f"V{p}" for p in rung)
        out[label] = pct

    return pd.DataFrame(out, index=df_eod_with_vwmas.index)