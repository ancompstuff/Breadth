import pandas as pd
from core.constants import mas_list, ma_groups


def build_vwma_ladders(df_eod_with_vwmas: pd.DataFrame, index_df: pd.DataFrame):
    """
    Returns:
        ladder: index Adj Close + 9 main ladder % columns (5 -> 200)
        mini_ladders: index Adj Close + 9 mini ladder % columns (s/m/l sets)

    Assumptions:
      - df_eod_with_vwmas has MultiIndex columns (level 0 are fields like 'Adj Close', 'VWMA5', ...)
      - index_df has a column 'Adj Close'
    """

    # --- basics
    assert "Adj Close" in df_eod_with_vwmas.columns.levels[0]
    assert "Adj Close" in index_df.columns

    adj = df_eod_with_vwmas.xs("Adj Close", level=0, axis=1)  # date x ticker
    n = adj.shape[1]  # number of tickers

    # Helper to fetch VWMA matrix
    def vwma(p):
        return df_eod_with_vwmas.xs(f"VWMA{p}", level=0, axis=1)

    # ------------------------------------------------------------
    # F1) MAIN LADDER (9 rungs) -> ladder dataframe
    # ------------------------------------------------------------
    ladder = pd.DataFrame(index=index_df.index)
    ladder["Adj Close"] = index_df["Adj Close"].reindex(ladder.index)

    # Build strict ladder incrementally:
    # start with price > VWMA5
    cond = adj > vwma(mas_list[0])
    rung = [mas_list[0]]
    ladder["$>V5%"] = cond.sum(axis=1) / n * 100.0

    # then keep AND-ing strict ordering: prev_vwma > next_vwma
    for p_prev, p_curr in zip(mas_list[:-1], mas_list[1:]):
        prev = vwma(p_prev)
        curr = vwma(p_curr)

        # strict structure extension
        cond = cond & (prev > curr)

        rung.append(p_curr)
        col = "$>" + ">".join(f"V{x}" for x in rung) + "%"
        ladder[col] = cond.sum(axis=1) / n * 100.0

    # Keep only the 9 rung columns (mas_list is already those 9 in your constants)
    # but this is safe if mas_list grows later:
    main_cols = []
    r = []
    for p in mas_list[:9]:
        r.append(p)
        main_cols.append("$>" + ">".join(f"V{x}" for x in r) + "%")
    ladder = ladder[["Adj Close"] + main_cols]

    # ------------------------------------------------------------
    # F2) MINI LADDERS -> mini_ladders dataframe (9 cols: s + m + l)
    # ------------------------------------------------------------
    mini_ladders = pd.DataFrame(index=index_df.index)
    mini_ladders["Adj Close"] = index_df["Adj Close"].reindex(mini_ladders.index)

    # short (s): just copy first 3 from ladder, prefix with s
    short3 = main_cols[:3]
    mini_ladders["s$>V5%"] = ladder[short3[0]]
    mini_ladders["s$>V5>V12%"] = ladder[short3[1]]
    mini_ladders["s$>V5>V12>V25%"] = ladder[short3[2]]

    # medium (m): independent ladder using ma_groups["medium"]["periods"] == [40,50,60]
    m1, m2, m3 = ma_groups["medium"]["periods"]
    m_base = adj > vwma(m1)                         # m$>V40
    m_2 = m_base & (vwma(m1) > vwma(m2))            # m$>V40>50
    m_3 = m_2 & (vwma(m2) > vwma(m3))               # m$>V40>50>60

    mini_ladders[f"m$>V{m1}%"] = m_base.sum(axis=1) / n * 100.0
    mini_ladders[f"m$>V{m1}>{m2}%"] = m_2.sum(axis=1) / n * 100.0
    mini_ladders[f"m$>V{m1}>{m2}>{m3}%"] = m_3.sum(axis=1) / n * 100.0

    # long (l): independent ladder using ma_groups["long"]["periods"] == [80,100,200]
    l1, l2, l3 = ma_groups["long"]["periods"]
    l_base = adj > vwma(l1)                         # l$>V80
    l_2 = l_base & (vwma(l1) > vwma(l2))            # l$>V80>100
    l_3 = l_2 & (vwma(l2) > vwma(l3))               # l$>V80>100>200

    mini_ladders[f"l$>V{l1}%"] = l_base.sum(axis=1) / n * 100.0
    mini_ladders[f"l$>V{l1}>{l2}%"] = l_2.sum(axis=1) / n * 100.0
    mini_ladders[f"l$>V{l1}>{l2}>{l3}%"] = l_3.sum(axis=1) / n * 100.0

    # align to index_df calendar
    ladder = ladder.reindex(index_df.index)
    mini_ladders = mini_ladders.reindex(index_df.index)

    return ladder, mini_ladders