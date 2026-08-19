"""
Aggregate TTM Squeeze + Volatility Cycle (components vs index).

This module follows the Breadth repo style:
- pure calculations only
- works with index_df (single columns) and components_df (MultiIndex columns)
- returns a date-indexed dataframe ready for plotting elsewhere

Definitions:
- TTM squeeze ON (per ticker): BB inside KC
- Aggregate squeeze: % of tickers with squeeze ON
- Volatility Cycle Ratio (per ticker): BB width / KC width
- Aggregate volatility cycle: median (or mean) of tickers' ratios
- Momentum (per ticker): rolling linreg endpoint of the standard TTM delta series
- Aggregate momentum: median (or mean) of tickers' momentum
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

import core.constants


AggMethod = Literal["mean", "median"]


def _get_price_cols() -> tuple[str, str, str]:
    """
    Resolve OHLC column names from constants if present, otherwise use repo conventions.
    """
    price_col = getattr(core.constants, "PRICE_COL", "Adj Close")
    high_col = getattr(core.constants, "HIGH_COL", "High")
    low_col = getattr(core.constants, "LOW_COL", "Low")
    return price_col, high_col, low_col


def _rolling_linreg_endpoint(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Rolling linear regression endpoint (value of fitted line at x=window-1) for each column.

    Uses rolling().apply with raw=True. This is not the fastest possible, but is explicit and robust.
    If you need speed later, we can vectorize further.
    """
    x = np.arange(window)

    def calc_end_point(y: np.ndarray) -> float:
        if len(y) < window or np.isnan(y).any():
            return np.nan
        slope, intercept = np.polyfit(x, y, 1)
        return slope * (window - 1) + intercept

    return df.rolling(window).apply(calc_end_point, raw=True)


def _compute_ttm_components(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    length: int,
    bb_mult: float,
    kc_mult: float,
    use_true_range: bool,
) -> dict[str, pd.DataFrame]:
    """
    Compute BB, KC, squeeze flag, VC ratio, and TTM momentum for a panel of tickers (columns=tickers).
    """
    sma = close.rolling(window=length).mean()
    stdev = close.rolling(window=length).std()

    bb_upper = sma + bb_mult * stdev
    bb_lower = sma - bb_mult * stdev

    if use_true_range:
        h_l = high - low
        h_pc = (high - close.shift(1)).abs()
        l_pc = (low - close.shift(1)).abs()
        tr = pd.concat([h_l, h_pc, l_pc], axis=1).groupby(level=0, axis=1).max() if isinstance(h_l.columns, pd.MultiIndex) else np.maximum.reduce([h_l, h_pc, l_pc])  # defensive
        # If not MultiIndex columns, tr already DataFrame with same columns as tickers
        if isinstance(tr, pd.DataFrame) is False:
            tr = pd.DataFrame(tr, index=close.index, columns=close.columns)
        atr = tr.rolling(window=length).mean()
    else:
        atr = (high - low).rolling(window=length).mean()

    kc_upper = sma + kc_mult * atr
    kc_lower = sma - kc_mult * atr

    squeeze_on = ((bb_upper < kc_upper) & (bb_lower > kc_lower)).astype(int)

    bb_width = bb_upper - bb_lower
    kc_width = kc_upper - kc_lower
    vc_ratio = bb_width / kc_width.replace(0, np.nan)

    # TTM Momentum delta definition: close - average( Donchian_mid, SMA )
    donchian_mid = (high.rolling(window=length).max() + low.rolling(window=length).min()) / 2.0
    delta = close - ((donchian_mid + sma) / 2.0)

    ttm_mom = _rolling_linreg_endpoint(delta, window=length)

    return {
        "sma": sma,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "kc_upper": kc_upper,
        "kc_lower": kc_lower,
        "squeeze_on": squeeze_on,
        "vc_ratio": vc_ratio,
        "ttm_mom": ttm_mom,
    }


def _agg(df: pd.DataFrame, method: AggMethod) -> pd.Series:
    if method == "median":
        return df.median(axis=1, skipna=True)
    if method == "mean":
        return df.mean(axis=1, skipna=True)
    raise ValueError(f"Unknown agg method: {method}")


def compute_aggregate_ttm_squeeze(
    index_df: pd.DataFrame,
    components_df: pd.DataFrame,
    *,
    length: int | None = None,
    bb_mult: float | None = None,
    kc_mult: float | None = None,
    use_true_range: bool | None = None,
    agg_method: AggMethod = "median",
) -> pd.DataFrame:
    """
    Compute aggregate TTM squeeze metrics for index + components.

    Returns a date-indexed DataFrame with columns:
      - idx_ttm_squeeze_on (0/1)
      - idx_volatility_cycle_ratio
      - idx_ttm_momentum
      - comp_squeeze_pct (0..100)
      - comp_volatility_cycle_ratio_{agg_method}
      - comp_ttm_momentum_{agg_method}
      - comp_volatility_cycle_ratio_p10 / p90  (useful bands)
      - comp_ttm_momentum_p10 / p90
    """
    price_col, high_col, low_col = _get_price_cols()

    # pull defaults from constants if user didn't override
    ttm_defaults = getattr(core.constants, "TTM_SQUEEZE_DEFAULTS", {})
    length = int(length if length is not None else ttm_defaults.get("length", 20))
    bb_mult = float(bb_mult if bb_mult is not None else ttm_defaults.get("bb_mult", 2.0))
    kc_mult = float(kc_mult if kc_mult is not None else ttm_defaults.get("kc_mult", 1.5))
    use_true_range = bool(use_true_range if use_true_range is not None else ttm_defaults.get("use_true_range", True))

    out = pd.DataFrame(index=index_df.index)

    # -----------------------
    # 1) Index-level TTM
    # -----------------------
    idx_close = index_df[price_col].copy()
    idx_high = index_df[high_col].copy()
    idx_low = index_df[low_col].copy()

    idx_panel = _compute_ttm_components(
        high=idx_high.to_frame("IDX"),
        low=idx_low.to_frame("IDX"),
        close=idx_close.to_frame("IDX"),
        length=length,
        bb_mult=bb_mult,
        kc_mult=kc_mult,
        use_true_range=use_true_range,
    )

    out["idx_ttm_squeeze_on"] = idx_panel["squeeze_on"]["IDX"]
    out["idx_volatility_cycle_ratio"] = idx_panel["vc_ratio"]["IDX"]
    out["idx_ttm_momentum"] = idx_panel["ttm_mom"]["IDX"]

    # -----------------------------------------
    # 2) Component-level TTM (panel by ticker)
    # -----------------------------------------
    if not isinstance(components_df.columns, pd.MultiIndex):
        raise TypeError("components_df must have MultiIndex columns (level0=field, level1=ticker).")

    high = components_df[high_col]
    low = components_df[low_col]
    close = components_df[price_col]

    comp_panel = _compute_ttm_components(
        high=high,
        low=low,
        close=close,
        length=length,
        bb_mult=bb_mult,
        kc_mult=kc_mult,
        use_true_range=use_true_range,
    )

    squeeze_on = comp_panel["squeeze_on"]
    vc_ratio = comp_panel["vc_ratio"]
    ttm_mom = comp_panel["ttm_mom"]

    # Aggregate squeeze %
    out["comp_squeeze_pct"] = 100.0 * squeeze_on.mean(axis=1, skipna=True)

    # Aggregate VC ratio (central tendency + bands)
    out[f"comp_volatility_cycle_ratio_{agg_method}"] = _agg(vc_ratio, agg_method)
    out["comp_volatility_cycle_ratio_p10"] = vc_ratio.quantile(0.10, axis=1, interpolation="linear")
    out["comp_volatility_cycle_ratio_p90"] = vc_ratio.quantile(0.90, axis=1, interpolation="linear")

    # Aggregate momentum (central tendency + bands)
    out[f"comp_ttm_momentum_{agg_method}"] = _agg(ttm_mom, agg_method)
    out["comp_ttm_momentum_p10"] = ttm_mom.quantile(0.10, axis=1, interpolation="linear")
    out["comp_ttm_momentum_p90"] = ttm_mom.quantile(0.90, axis=1, interpolation="linear")

    # Helpful binary "broad squeeze regime" threshold, configurable via constants
    squeeze_regime_thresh = float(ttm_defaults.get("squeeze_regime_threshold_pct", 20.0))
    out["comp_squeeze_regime_on"] = (out["comp_squeeze_pct"] >= squeeze_regime_thresh).astype(int)

    return out