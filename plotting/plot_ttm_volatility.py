"""
Plotting for aggregate TTM squeeze + volatility cycle.

- No calculations here.
- Uses PlotSetup to standardize x-axis + price background layer.
- Returns matplotlib Figure.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

import core.constants
from core.my_data_types import PlotSetup


def plot_aggregate_ttm_squeeze(ps: PlotSetup, df_in: pd.DataFrame) -> plt.Figure:
    """
    Expected columns (from indicators.ttm_squeeze.compute_aggregate_ttm_squeeze):
      - idx_ttm_squeeze_on
      - idx_volatility_cycle_ratio
      - idx_ttm_momentum
      - comp_squeeze_pct
      - comp_squeeze_regime_on
      - comp_volatility_cycle_ratio_{median|mean}
      - comp_volatility_cycle_ratio_p10 / p90
      - comp_ttm_momentum_{median|mean}
      - comp_ttm_momentum_p10 / p90
    """
    df = df_in.loc[ps.price_data.index].copy()

    ttm_defaults = getattr(core.constants, "TTM_SQUEEZE_DEFAULTS", {})
    squeeze_regime_thresh = float(ttm_defaults.get("squeeze_regime_threshold_pct", 20.0))

    # detect which agg method column exists
    vc_col = None
    mom_col = None
    for m in ("median", "mean"):
        cand_vc = f"comp_volatility_cycle_ratio_{m}"
        cand_mom = f"comp_ttm_momentum_{m}"
        if cand_vc in df.columns:
            vc_col = cand_vc
        if cand_mom in df.columns:
            mom_col = cand_mom

    if vc_col is None or mom_col is None:
        raise KeyError("Could not find aggregate VC/momentum columns. Did you pass the correct dataframe?")

    fig, axes = plt.subplots(
        nrows=4,
        ncols=1,
        figsize=(core.constants.FIG_W, core.constants.FIG_H) if hasattr(core.constants, "FIG_W") else (14, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0, 1.2, 1.2]},
    )

    ax_price, ax_squeeze, ax_vc, ax_mom = axes

    # ----------------
    # 1) Price layer
    # ----------------
    ps.plot_price_layer(ax_price)
    ax_price.set_title(f"{ps.idx} — Aggregate TTM Squeeze / Volatility Cycle")

    # -----------------------------
    # 2) Squeeze participation (%)
    # -----------------------------
    x = ps.plot_index

    ax_squeeze.plot(x, df["comp_squeeze_pct"], label="% Components in Squeeze", color="tab:red", lw=1.5)
    ax_squeeze.axhline(squeeze_regime_thresh, color="tab:red", ls="--", lw=1.0, alpha=0.7)
    ax_squeeze.set_ylabel("% in squeeze")
    ax_squeeze.set_ylim(0, 100)
    ax_squeeze.grid(True, alpha=0.25)

    # regime shading (broad squeeze)
    if "comp_squeeze_regime_on" in df.columns:
        on = df["comp_squeeze_regime_on"].fillna(0).astype(int).values
        ax_squeeze.fill_between(x, 0, 100, where=on == 1, color="tab:red", alpha=0.08, step=None)

    # -------------------------
    # 3) Volatility cycle ratio
    # -------------------------
    ax_vc.plot(x, df[vc_col], label=f"VC Ratio ({vc_col.split('_')[-1]})", color="tab:blue", lw=1.5)
    if "comp_volatility_cycle_ratio_p10" in df.columns and "comp_volatility_cycle_ratio_p90" in df.columns:
        ax_vc.fill_between(
            x,
            df["comp_volatility_cycle_ratio_p10"],
            df["comp_volatility_cycle_ratio_p90"],
            color="tab:blue",
            alpha=0.12,
            label="VC p10–p90",
        )
    ax_vc.axhline(1.0, color="black", lw=1.0, ls="--", alpha=0.6)
    ax_vc.set_ylabel("BB/KC")
    ax_vc.grid(True, alpha=0.25)

    # ---------------------------------
    # 4) Momentum (aggregate + interval)
    # ---------------------------------
    ax_mom.plot(x, df[mom_col], label=f"TTM Momentum ({mom_col.split('_')[-1]})", color="tab:green", lw=1.5)
    if "comp_ttm_momentum_p10" in df.columns and "comp_ttm_momentum_p90" in df.columns:
        ax_mom.fill_between(
            x,
            df["comp_ttm_momentum_p10"],
            df["comp_ttm_momentum_p90"],
            color="tab:green",
            alpha=0.12,
            label="Mom p10–p90",
        )
    ax_mom.axhline(0.0, color="black", lw=1.0, ls="--", alpha=0.6)
    ax_mom.set_ylabel("momentum")
    ax_mom.grid(True, alpha=0.25)

    # common x-axis formatting
    ps.apply_xaxis(ax_mom)
    for ax in axes[:-1]:
        ax.set_xlim(ps.plot_index.min(), ps.plot_index.max())

    ax_squeeze.legend(loc="upper left", fontsize=9)
    ax_vc.legend(loc="upper left", fontsize=9)
    ax_mom.legend(loc="upper left", fontsize=9)

    fig.tight_layout()
    return fig