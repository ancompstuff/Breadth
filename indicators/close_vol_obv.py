import numpy as np
import pandas as pd


def compute_close_vol_obv(index_df: pd.DataFrame, components_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Close/Volume/OBV indicators for:
      - the index (from index_df)
      - an aggregate of all component tickers (from components_df)

    components_df must have MultiIndex columns with level 0 containing:
      ['Adj Close', 'Volume', 'High', 'Low']
    and level 1 being ticker symbols.

    Returns a DataFrame indexed by date with:
      Index: OBV, NMF_cum, normalized versions, bullish/bearish flags/strengths
      Components aggregate: OBV_mean_norm, NMF_mean_norm, and flags/strengths
    """

    out = pd.DataFrame(index=index_df.index)

    # -------------------
    # 1) INDEX OBV + NMF
    # -------------------
    idx = index_df.copy()

    direction = np.where(idx["Adj Close"].diff().fillna(0) > 0, 1, -1)
    idx_obv = (direction * idx["Volume"] * idx["Adj Close"]).cumsum()

    typical = (idx["High"] + idx["Low"] + idx["Adj Close"]) / 3
    money_flow = typical * idx["Volume"]

    idx_nmf = np.where(
        typical.diff() > 0,
        money_flow,
        np.where(typical.diff() < 0, -money_flow, 0),
    )
    idx_nmf_cum = pd.Series(idx_nmf, index=idx.index).cumsum()

    # normalize index series to 0-1 for plotting
    idx_obv_norm = (idx_obv - idx_obv.min()) / (idx_obv.max() - idx_obv.min())
    idx_nmf_norm = (idx_nmf_cum - idx_nmf_cum.min()) / (idx_nmf_cum.max() - idx_nmf_cum.min())

    out["Adj Close"] = idx["Adj Close"]
    out["Volume"] = idx["Volume"]
    out["OBV"] = idx_obv
    out["NMF_cum"] = idx_nmf_cum
    out["OBV_norm"] = idx_obv_norm
    out["NMF_norm"] = idx_nmf_norm

    obv_ch = out["OBV_norm"].diff()
    nmf_ch = out["NMF_norm"].diff()

    out["Bearish"] = ((obv_ch < 0) & (nmf_ch < 0)).astype(int)
    out["Bullish"] = ((obv_ch > 0) & (nmf_ch > 0)).astype(int)
    out["BearStrength"] = (-obv_ch.clip(upper=0)) + (-nmf_ch.clip(upper=0))
    out["BullStrength"] = (obv_ch.clip(lower=0)) + (nmf_ch.clip(lower=0))

    # ------------------------------------------
    # 2) COMPONENTS: per-ticker OBV + NMF (agg)
    # ------------------------------------------
    required = ["Adj Close", "Volume", "High", "Low"]
    for f in required:
        if f not in components_df.columns.levels[0]:
            raise KeyError(f"components_df is missing field '{f}' in column level 0")

    c_adj = components_df.xs("Adj Close", level=0, axis=1)
    c_vol = components_df.xs("Volume", level=0, axis=1)
    c_high = components_df.xs("High", level=0, axis=1)
    c_low = components_df.xs("Low", level=0, axis=1)

    # OBV per ticker
    c_dir = np.where(c_adj.diff().fillna(0) > 0, 1, -1)  # ndarray aligned to c_adj
    c_obv = (pd.DataFrame(c_dir, index=c_adj.index, columns=c_adj.columns) * c_vol * c_adj).cumsum()

    # NMF per ticker
    c_typical = (c_high + c_low + c_adj) / 3
    c_money_flow = c_typical * c_vol

    c_nmf = np.where(
        c_typical.diff() > 0,
        c_money_flow,
        np.where(c_typical.diff() < 0, -c_money_flow, 0),
    )
    c_nmf = pd.DataFrame(c_nmf, index=c_adj.index, columns=c_adj.columns)
    c_nmf_cum = c_nmf.cumsum()

    # normalize per ticker to 0-1 (so each ticker contributes equally)
    c_obv_min = c_obv.min(axis=0)
    c_obv_max = c_obv.max(axis=0)
    c_obv_norm = (c_obv - c_obv_min) / (c_obv_max - c_obv_min)

    c_nmf_min = c_nmf_cum.min(axis=0)
    c_nmf_max = c_nmf_cum.max(axis=0)
    c_nmf_norm = (c_nmf_cum - c_nmf_min) / (c_nmf_max - c_nmf_min)

    # aggregate: mean across tickers each day (skip NaNs)
    out["Comp_OBV_norm_mean"] = c_obv_norm.mean(axis=1)
    out["Comp_NMF_norm_mean"] = c_nmf_norm.mean(axis=1)

    comp_obv_ch = out["Comp_OBV_norm_mean"].diff()
    comp_nmf_ch = out["Comp_NMF_norm_mean"].diff()

    out["Comp_Bearish"] = ((comp_obv_ch < 0) & (comp_nmf_ch < 0)).astype(int)
    out["Comp_Bullish"] = ((comp_obv_ch > 0) & (comp_nmf_ch > 0)).astype(int)
    out["Comp_BearStrength"] = (-comp_obv_ch.clip(upper=0)) + (-comp_nmf_ch.clip(upper=0))
    out["Comp_BullStrength"] = (comp_obv_ch.clip(lower=0)) + (comp_nmf_ch.clip(lower=0))

    return out