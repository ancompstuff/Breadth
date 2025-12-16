import pandas as pd
from core.constants import mas_list, trend_combinations

# =====================================================================
# 1. VWMA BREADTH (%>VWMA, %<VWMA)
# =====================================================================
def build_vwma_trend_counts_and_percents(
    df_eod_with_vwmas: pd.DataFrame,
) -> pd.DataFrame:
    """
    Builds classic VWMA breadth series.

    Output columns:
        Nº>VWMA5, %>VWMA5
        Nº<VWMA5, %<VWMA5
        ...
    """

    assert "Adj Close" in df_eod_with_vwmas.columns.levels[0]

    adj = df_eod_with_vwmas.xs("Adj Close", level=0, axis=1)
    n_tickers = adj.shape[1]

    out = {}

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
    """
    Enforces a TRUE ladder:

        price > v0 > v1 > v2 > ...

    Nothing else is checked.
    """

    cond = adj > vwmas[0]

    for prev, curr in zip(vwmas[:-1], vwmas[1:]):
        cond &= prev > curr

    return cond


# =====================================================================
# 3. TRUE VWMA LADDERS (MAIN + MINI)
# =====================================================================
def build_vwma_true_ladders(
    df_eod_with_vwmas: pd.DataFrame,
) -> pd.DataFrame:
    """
    Builds TRUE VWMA ladders.

    MAIN ladder:
        VWMA5 → VWMA200 (using mas_list order)

    MINI ladders:
        From trend_combinations (e.g. VWMA40→60, VWMA80→200)

    Output columns (examples):
        $>V5
        $>V5>V12
        $>V5>V12>V25
        ...
        $>V40>V50 (medium)
        $>V80>V100>V200 (long)
    """

    assert "Adj Close" in df_eod_with_vwmas.columns.levels[0]

    adj = df_eod_with_vwmas.xs("Adj Close", level=0, axis=1)
    n_tickers = adj.shape[1]

    out = {}

    # ---------------------------------------------------------------
    # MAIN LADDER (mas_list)
    # ---------------------------------------------------------------
    for i in range(len(mas_list)):
        rung = mas_list[: i + 1]

        vwmas = [
            df_eod_with_vwmas.xs(f"VWMA{p}", level=0, axis=1)
            for p in rung
        ]

        cond = _strict_ladder_condition(adj, vwmas)
        pct = cond.sum(axis=1) / n_tickers * 100.0

        label = "$>" + ">".join(f"V{p}" for p in rung)
        out[label] = pct

    # ---------------------------------------------------------------
    # MINI LADDERS (trend_combinations)
    # ---------------------------------------------------------------
    for name, fields in trend_combinations.items():
        periods = [int(f.replace("VWMA", "")) for f in fields]

        for i in range(len(periods)):
            rung = periods[: i + 1]

            vwmas = [
                df_eod_with_vwmas.xs(f"VWMA{p}", level=0, axis=1)
                for p in rung
            ]

            cond = _strict_ladder_condition(adj, vwmas)
            pct = cond.sum(axis=1) / n_tickers * 100.0

            label = "$>" + ">".join(f"V{p}" for p in rung)
            out[f"{label} ({name})"] = pct

    return pd.DataFrame(out, index=df_eod_with_vwmas.index)
