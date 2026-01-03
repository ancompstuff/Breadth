from __future__ import annotations

"""
breakout_indicators.py

Purpose
-------
Compute “breakout” and “breakdown” signals from adjusted close price data, append
those signals to the EOD (end-of-day) panel, and produce an index/summary table
(df_idx_out) containing:
- per-condition counts (how many tickers triggered each signal each day)
- group totals (Total_Breakouts / Total_Breakdowns)
- moving averages of totals
- normalization to percent-of-active-tickers (participation)
- regime/timing helpers (impulse, risk-on flag, thrust z-score)
- ratio features (UP vs DOWN over configurable windows)

Data Expectations (Important)
-----------------------------
df_eod is expected to be a *wide panel* of price fields where:
- columns are a pandas MultiIndex
  - level 0: price field name (e.g. "Adj Close")
  - level 1: ticker symbol (e.g. "AAPL", "MSFT", ...)
- index is datetime-like trading days

Example df_eod columns:
    ("Adj Close", "AAPL"), ("Adj Close", "MSFT"), ...
    ("Open", "AAPL"), ("Open", "MSFT"), ...

df_idx is a time-indexed DataFrame (same index as df_eod) used to store summary
series (counts, MAs, z-scores, etc.). It typically has one column per indicator.

Notes on BreakoutCondition
--------------------------
BreakoutCondition is assumed to provide at least:
- plot_group: int (used to decide which conditions roll into “Total_*”)
- period_days: int (lookback horizon for pct_change)
- pct: float (threshold, e.g. 0.04 for 4%)
- up_col: str (column name for the “up breakout” signal series, e.g. "UP_1d_4%")
- down_col: str (column name for the “down breakdown” signal series)
- color: str (not used in computations here; likely for plotting)

Signal Semantics
----------------
For each ticker and each condition:
- pctchg = close.pct_change(periods=period_days)

“Up breakout event” occurs on the first day pctchg crosses from below threshold
to >= threshold:
    up_mask = 1 when:
        pctchg[t]   >=  pct
    AND pctchg[t-1] <  pct

“Down breakdown event” occurs on the first day pctchg crosses from above
(-pct) to <= (-pct):
    down_mask = 1 when:
        pctchg[t]   <= -pct
    AND pctchg[t-1] >  -pct

This “crossing” logic prevents long streaks of 1s when the return remains above
the threshold for several consecutive days.

Outputs
-------
(df_idx_out, df_eod_out)

- df_eod_out: df_eod with extra MultiIndex columns added for each condition’s
  up/down event masks. Each new field is a top-level column (level 0) whose
  second level is the ticker.
  Example added columns:
      ("UP_1d_4%", "AAPL"), ("UP_1d_4%", "MSFT"), ...
      ("DOWN_1d_4%", "AAPL"), ...

- df_idx_out: df_idx with:
  - counts per event type (sum across tickers)
  - totals across plot_group == 1 conditions
  - MAs and percent participation
  - impulse/regime helpers
  - thrust z-score and flag
  - ratio features

Caveats / Known Constraints
---------------------------
- conditions must be non-empty because ratio features use the “first” condition.
- df_eod must include "Adj Close" at MultiIndex level 0.
- If your df_eod does not use a MultiIndex, you must adapt the input or this
  function.
"""

from typing import Optional, Iterable
import pandas as pd

from core.constants import breakout_conditions, breakout_ma_window, breakout_ratio_windows
from core.my_data_types import BreakoutCondition


def add_breakout_columns(
    df_idx: pd.DataFrame,
    df_eod: pd.DataFrame,
    conditions: Optional[Iterable[BreakoutCondition]] = None,
    ma_window: int = breakout_ma_window,
    ratio_windows: tuple[int, int] = breakout_ratio_windows,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Add breakout/breakdown event columns to df_eod and summary/indicator columns to df_idx.

    Parameters
    ----------
    df_idx:
        Time-indexed “index / summary” DataFrame. Must share the same index as df_eod.
        Existing columns are preserved; new derived columns are appended.

    df_eod:
        MultiIndex-column DataFrame of EOD data. Must contain "Adj Close" in
        columns.levels[0]. The "Adj Close" slice should be a wide DataFrame of
        shape (n_days, n_tickers).

    conditions:
        Iterable of BreakoutCondition objects. If None, defaults to
        core.constants.breakout_conditions.

    ma_window:
        Rolling window size for moving average smoothing on aggregate series.

    ratio_windows:
        Two rolling windows (w1, w2) used to compute UP-vs-DOWN ratios for the
        “first” breakout condition.

    Returns
    -------
    (df_idx_out, df_eod_out):
        df_idx_out has aggregate and indicator columns.
        df_eod_out has the original EOD panel plus per-ticker event masks added.

    Raises
    ------
    KeyError:
        If df_eod does not contain "Adj Close" as a level-0 MultiIndex entry.
    IndexError:
        If conditions is empty (because ratio features use the first condition).
    """

    # -------------------------
    # 0) Defaults / copies
    # -------------------------
    if conditions is None:
        conditions = breakout_conditions

    # Create copies to avoid mutating caller data.
    df_eod_out = df_eod.copy()
    df_idx_out = df_idx.copy()

    # Validate the expected MultiIndex structure: we require a level-0 entry
    # called "Adj Close" so we can compute percentage changes.
    if "Adj Close" not in df_eod_out.columns.levels[0]:
        raise KeyError("df_eod must contain 'Adj Close' in MultiIndex level 0")

    # Extract adjusted close prices as a wide DataFrame (rows=dates, cols=tickers).
    close = df_eod_out["Adj Close"].copy()

    # We build event mask frames (one per condition) and concat them once at end.
    # This is generally faster than repeated df assignment in loops.
    up_frames: list[pd.DataFrame] = []
    down_frames: list[pd.DataFrame] = []
    up_names: list[str] = []
    down_names: list[str] = []

    # -------------------------
    # 1) Build per-ticker event masks for each condition
    # -------------------------
    for c in conditions:
        # These are extracted mostly for readability and debugging.
        # plot_group and color are not used for computation below (except group totals).
        plot_group = c.plot_group
        period = c.period_days
        pct = c.pct
        up_name = c.up_col
        down_name = c.down_col
        color = c.color

        # Percent change over the requested horizon.
        # fill_method=None avoids forward-filling NAs when computing pct_change.
        pctchg = close.pct_change(periods=period, fill_method=None)

        # “Crossing” detection:
        # - up_mask triggers once when crossing above +pct
        # - down_mask triggers once when crossing below -pct
        up_mask = ((pctchg >= pct) & (pctchg.shift(1) < pct)).astype("int")
        down_mask = ((pctchg <= -pct) & (pctchg.shift(1) > -pct)).astype("int")

        # Re-assign columns to a MultiIndex so these can live alongside df_eod’s
        # existing structure (level 0 = field name, level 1 = ticker).
        up_mask.columns = pd.MultiIndex.from_product([[up_name], up_mask.columns])
        down_mask.columns = pd.MultiIndex.from_product([[down_name], down_mask.columns])

        up_frames.append(up_mask)
        down_frames.append(down_mask)
        up_names.append(up_name)
        down_names.append(down_name)

    # Concatenate all new columns at once and append to df_eod_out.
    new_cols = pd.concat(up_frames + down_frames, axis=1)
    df_eod_out = pd.concat([df_eod_out, new_cols], axis=1)

    # -------------------------
    # 2) Aggregate: counts per day (sum across tickers)
    # -------------------------
    # After this step, df_idx_out has one column per event type (e.g. UP_1d_4%)
    # and each row is: number of tickers that triggered that event that day.
    for name in up_names + down_names:
        df_idx_out[name] = df_eod_out[name].sum(axis=1)

    # -------------------------
    # 3) Group totals (plot_group == 1)
    # -------------------------
    # Many users only want a “main” set of conditions to form the totals.
    group1_up = [c.up_col for c in conditions if c.plot_group == 1]
    group1_down = [c.down_col for c in conditions if c.plot_group == 1]

    # If there are no group-1 conditions, write 0 (scalar); pandas will broadcast.
    df_idx_out["Total_Breakouts"] = df_idx_out[group1_up].sum(axis=1) if group1_up else 0
    df_idx_out["Total_Breakdowns"] = df_idx_out[group1_down].sum(axis=1) if group1_down else 0

    # Simple moving averages of totals (smoothed breadth).
    df_idx_out["MA_Breakouts"] = df_idx_out["Total_Breakouts"].rolling(window=ma_window, min_periods=1).mean()
    df_idx_out["MA_Breakdowns"] = df_idx_out["Total_Breakdowns"].rolling(window=ma_window, min_periods=1).mean()

    # --------------------------------------------------------
    # 4) Normalize counts to % of active tickers
    # --------------------------------------------------------
    # Define "active tickers" as those with a non-null Adj Close on that day.
    # This handles symbol universe changes (IPOs, delistings) and missing data.
    adj = df_eod_out["Adj Close"]
    active_n = adj.notna().sum(axis=1).astype(float)

    # Avoid divide-by-zero (if all tickers are missing on a date).
    active_n = active_n.replace(0, pd.NA)

    df_idx_out["Active_Tickers"] = active_n

    # Participation metrics (% of active tickers triggering the event).
    # These can be more comparable across time than raw counts.
    df_idx_out["Pct_Total_Breakouts"] = df_idx_out["Total_Breakouts"] / active_n * 100.0
    df_idx_out["Pct_Total_Breakdowns"] = df_idx_out["Total_Breakdowns"] / active_n * 100.0

    # Net participation: breakout participation minus breakdown participation.
    df_idx_out["Pct_Impulse_Breakouts"] = (
        df_idx_out["Pct_Total_Breakouts"] - df_idx_out["Pct_Total_Breakdowns"]
    )

    # Smoothed % series.
    df_idx_out["MA_Pct_Total_Breakouts"] = (
        df_idx_out["Pct_Total_Breakouts"].rolling(window=ma_window, min_periods=1).mean()
    )
    df_idx_out["MA_Pct_Total_Breakdowns"] = (
        df_idx_out["Pct_Total_Breakdowns"].rolling(window=ma_window, min_periods=1).mean()
    )
    df_idx_out["MA_Pct_Impulse_Breakouts"] = (
        df_idx_out["Pct_Impulse_Breakouts"].rolling(window=ma_window, min_periods=1).mean()
    )

    # -----------------------------
    # 5) Timing/regime series (swing-trading helpers)
    # -----------------------------
    # “Impulse” answers: are breakouts dominating breakdowns?
    df_idx_out["Impulse_Breakouts"] = (
        df_idx_out["Total_Breakouts"] - df_idx_out["Total_Breakdowns"]
    )

    # Smoothed impulse.
    df_idx_out["MA_Impulse_Breakouts"] = (
        df_idx_out["Impulse_Breakouts"].rolling(window=ma_window, min_periods=1).mean()
    )

    # Simple regime flag (1 when smoothed impulse is positive).
    df_idx_out["Regime_RiskOn"] = (df_idx_out["MA_Impulse_Breakouts"] > 0).astype(int)

    # Thrust marker: broad breakout participation relative to a long baseline.
    # Rolling 252 trading days ~ 1 year.
    base = df_idx_out["Total_Breakouts"].rolling(window=252, min_periods=20)
    mu = base.mean()
    sd = base.std(ddof=0).replace(0, pd.NA)  # avoid divide-by-zero if sd=0

    df_idx_out["Z_Thrust_Breakouts"] = (df_idx_out["Total_Breakouts"] - mu) / sd
    df_idx_out["Flag_Thrust_Breakouts"] = (df_idx_out["Z_Thrust_Breakouts"] >= 2.0).astype(int)

    # -----------------------------
    # 6) Ratio features for the first condition
    # -----------------------------
    # The code assumes the first condition is the "primary" one (often 1d/4%),
    # and builds ratios of rolling UP counts divided by rolling DOWN counts.
    #
    # If conditions is empty, this will raise IndexError. If you want a safer
    # behavior, guard with: if not list(conditions): ...
    first = list(conditions)[0]
    up0 = first.up_col
    down0 = first.down_col

    w1, w2 = ratio_windows

    up_w1 = df_idx_out[up0].rolling(window=w1, min_periods=1).sum()
    down_w1 = df_idx_out[down0].rolling(window=w1, min_periods=1).sum()
    up_w2 = df_idx_out[up0].rolling(window=w2, min_periods=1).sum()
    down_w2 = df_idx_out[down0].rolling(window=w2, min_periods=1).sum()

    # Replace 0 denominator with NA to avoid infinite ratios.
    df_idx_out[f"RATIO_{w1}d_UPvsDOWN_{up0.replace('UP_', '')}"] = up_w1 / down_w1.replace(0, pd.NA)
    df_idx_out[f"RATIO_{w2}d_UPvsDOWN_{up0.replace('UP_', '')}"] = up_w2 / down_w2.replace(0, pd.NA)

    return df_idx_out, df_eod_out


if __name__ == "__main__":
    """
    Print the ACTUAL columns returned by add_breakout_columns() using cached inputs.

    This resolves paths relative to this file (not the current working directory),
    so it works when launched from PyCharm or from anywhere.

    Expected cache location (relative to repo root):
      Structured_Breadth/data_cache/index_df.parquet
      Structured_Breadth/data_cache/components_df.parquet
    """
    from pathlib import Path
    import pandas as pd

    # This file: .../Structured_Breadth/indicators/breakout_indicators.py
    # Repo root: .../Structured_Breadth
    repo_root = Path(__file__).resolve().parents[1]

    cache_dir = repo_root / "data_cache"
    idx_path = cache_dir / "index_df.parquet"
    eod_path = cache_dir / "components_df.parquet"

    if not idx_path.exists() or not eod_path.exists():
        raise SystemExit(
            "Missing cached parquet files.\n"
            "Run main.py once to generate:\n"
            f"  - {idx_path}\n"
            f"  - {eod_path}\n"
        )

    df_idx = pd.read_parquet(idx_path)
    df_eod = pd.read_parquet(eod_path)

    df_idx_out, df_eod_out = add_breakout_columns(df_idx, df_eod)

    print("\n=== df_idx_out.columns (returned) ===")
    for i, col in enumerate(df_idx_out.columns.tolist(), 1):
        print(f"{i:03d}. {col}")

    print("\n=== df_eod_out columns (returned) ===")
    if isinstance(df_eod_out.columns, pd.MultiIndex):
        # Most readable: show top-level field names (level 0).
        lvl0 = df_eod_out.columns.get_level_values(0).unique().tolist()
        print("\n--- MultiIndex level 0 fields ---")
        for i, field in enumerate(lvl0, 1):
            print(f"{i:03d}. {field}")

        # Optional: if you really want ALL MultiIndex tuples, uncomment below.
        # print("\n--- Full MultiIndex column tuples ---")
        # for i, tup in enumerate(df_eod_out.columns.tolist(), 1):
        #     print(f"{i:05d}. {tup}")
    else:
        for i, col in enumerate(df_eod_out.columns.tolist(), 1):
            print(f"{i:03d}. {col}")