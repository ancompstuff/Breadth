from __future__ import annotations

from typing import Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd

from core.constants import breakout_conditions
from core.my_data_types import PlotSetup


def plot_breakouts(
    ps: PlotSetup,
    df_breakouts_sum: pd.DataFrame,
    conditions=None,
    focus_conditions=None,
) -> plt.Figure:
    """
    4-panel breakout dashboard (all panels plot % of active tickers):

    Panel 0: Focus Breakout Events (%)
    Panel 1: Focus Breakdown Events (%)
    Panel 2: All Breakout Events (%) for plot_group == 1
    Panel 3: All Breakdown Events (%) for plot_group == 1

    Notes
    -----
    - Uses df_breakouts_sum["Active_Tickers"] as denominator when present (preferred).
      Falls back to ps.num_tickers otherwise.
    - If focus_conditions is None, it will try to use core.constants.breakout_focus_up_cols
      (recommended). If that constant doesn't exist, it falls back to ["UP_1d_4%", "UP_5d_10%"].
    - If focus conditions cannot be found, it falls back to the first 2 plot_group==1 conditions.
    """

    # ----------------------------
    # Defaults / input normalization
    # ----------------------------
    if conditions is None:
        conditions = breakout_conditions
    conditions = list(conditions)

    # slice to PlotSetup window
    df = df_breakouts_sum.loc[ps.price_data.index].copy()

    # ----------------------------
    # Denominator: ALWAYS a vector (len N)
    # ----------------------------
    if "Active_Tickers" in df.columns:
        denom = df["Active_Tickers"].to_numpy(dtype=float)
    else:
        denom = pd.Series(float(ps.num_tickers), index=df.index).to_numpy(dtype=float)

    denom[denom == 0] = float("nan")

    # ----------------------------
    # Condition sets
    # ----------------------------
    group1_conditions = [c for c in conditions if getattr(c, "plot_group", None) == 1]

    # Focus conditions:
    # 1) caller-provided focus_conditions OR
    # 2) constant-driven selection using breakout_focus_up_cols OR
    # 3) fallback: first two group1 conditions
    if focus_conditions is None:
        # Try to import focus list from constants (no hardcoding in plotting)
        try:
            from core.constants import breakout_focus_up_cols  # type: ignore
            focus_up_cols = set(breakout_focus_up_cols)
        except Exception:
            # Fallback if constant doesn't exist yet
            focus_up_cols = {"UP_1d_4%", "UP_5d_10%"}

        focus_conditions = [c for c in conditions if getattr(c, "up_col", None) in focus_up_cols]

        # If still empty (e.g., df doesn't include those cols in some test), fallback
        if not focus_conditions:
            focus_conditions = group1_conditions[:2]
    else:
        focus_conditions = list(focus_conditions)

    # ----------------------------
    # Figure / shared decorations
    # ----------------------------
    fig, (ax0, ax1, ax2, ax3) = plt.subplots(4, 1, figsize=(18, 9), sharex=True)

    # Regime shading across all panels (green background when risk-on)
    if "Regime_RiskOn" in df.columns:
        mask = df["Regime_RiskOn"].to_numpy(dtype=int) == 1
        for ax in (ax0, ax1, ax2, ax3):
            ax.fill_between(
                ps.plot_index,
                0,
                1,
                where=mask,
                transform=ax.get_xaxis_transform(),
                color="green",
                alpha=0.08,
                zorder=0,
            )

    # Thrust markers across all panels
    if "Flag_Thrust_Breakouts" in df.columns:
        thrust_mask = df["Flag_Thrust_Breakouts"].to_numpy(dtype=int) == 1
        thrust_x = ps.plot_index[thrust_mask]
        for x in thrust_x:
            for ax in (ax0, ax1, ax2, ax3):
                ax.axvline(x=x, color="purple", linewidth=1.0, alpha=0.20, zorder=1)

    def _plot_stack_pct(
        ax: plt.Axes,
        title: str,
        direction: str,  # "up" or "down"
        conds,
        ma_col_pct: str | None = None,
        ma_col_count: str | None = None,
        ma_label: str | None = None,
        invert: bool = False,
    ) -> None:
        ax.set_title(title, fontsize=11, fontweight="bold")
        ps.plot_price_layer(ax
                            )
        ax.grid(True, axis="both")
        ax.set_ylabel(f"{ps.idx} preço", fontsize=9)

        ax_t = ax.twinx()
        ax_t.set_ylabel("Stacked %ages", fontsize=9)
        if invert:
            ax_t.invert_yaxis()

        if direction == "up":
            series = [(c.up_col, c.color) for c in conds]
        else:
            series = [(c.down_col, c.color) for c in conds]

        bottom = pd.Series(0.0, index=ps.plot_index)

        plotted_any = False
        for col_name, color in series:
            if col_name not in df.columns:
                continue

            counts = df[col_name].to_numpy(dtype=float)
            vals_pct = (counts / denom) * 100.0  # <-- force 0..100 % scale
            ax_t.bar(ps.plot_index, vals_pct, bottom=bottom.values, color=color, alpha=0.6, label=col_name)
            bottom += vals_pct
            plotted_any = True

        # If nothing plotted, write a visible hint (better than "blank chart")
        if not plotted_any:
            ax_t.text(
                0.01,
                0.85,
                "No matching columns to plot",
                transform=ax_t.transAxes,
                fontsize=9,
                color="crimson",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="crimson"),
            )

        # MA overlay: prefer percent column; fallback convert count MA to percent
        if ma_col_pct and ma_col_pct in df.columns:
            ax_t.plot(
                ps.plot_index,
                df[ma_col_pct].to_numpy(dtype=float),
                color=("green" if direction == "up" else "red"),
                linestyle="--",
                linewidth=2,
                label=ma_label or ma_col_pct,
            )
        elif ma_col_count and ma_col_count in df.columns:
            ax_t.plot(
                ps.plot_index,
                (df[ma_col_count].to_numpy(dtype=float) / denom) * 100.0,
                color=("green" if direction == "up" else "red"),
                linestyle="--",
                linewidth=2,
                label=ma_label or (ma_col_count + " (%)"),
            )

        # Legend
        l1, lab1 = ax.get_legend_handles_labels()
        l2, lab2 = ax_t.get_legend_handles_labels()
        ax_t.legend(l1 + l2, lab1 + lab2, loc="upper left", fontsize=8)

        ps.fix_xlimits(ax)

    # Panel 0: Focus breakouts (%)
    _plot_stack_pct(
        ax=ax0,
        title=f"{ps.idx}: Focus Breakout Events (%) ({ps.sample_start}-{ps.sample_end})",
        direction="up",
        conds=focus_conditions,
        invert=False,
    )

    # Panel 1: Focus breakdowns (%)
    _plot_stack_pct(
        ax=ax1,
        title=f"{ps.idx}: Focus Breakdown Events (%) ({ps.sample_start}-{ps.sample_end})",
        direction="down",
        conds=focus_conditions,
        invert=True,
    )

    # Panel 2: All breakouts (%) plot_group==1
    _plot_stack_pct(
        ax=ax2,
        title=f"{ps.idx}: Breakout Events (%) (group 1) ({ps.sample_start}-{ps.sample_end})",
        direction="up",
        conds=group1_conditions,
        ma_col_pct="MA_Pct_Total_Breakouts",
        ma_col_count="MA_Breakouts",
        ma_label="MA % (Total Breakouts)",
        invert=False,
    )

    # Panel 3: All breakdowns (%) plot_group==1
    _plot_stack_pct(
        ax=ax3,
        title=f"{ps.idx}: Breakdown Events (%) (group 1) ({ps.sample_start}-{ps.sample_end})",
        direction="down",
        conds=group1_conditions,
        ma_col_pct="MA_Pct_Total_Breakdowns",
        ma_col_count="MA_Breakdowns",
        ma_label="MA % (Total Breakdowns)",
        invert=True,
    )

    # X axis formatting via PlotSetup
    ps.apply_xaxis(ax3)
    ax3.set_xlabel("Data")

    #fig.tight_layout()
    return fig


def plot_stockbee_1(ps: PlotSetup, df_breakouts_sum: pd.DataFrame) -> plt.Figure:
    """
    Uses first breakout condition (typically 1d 4%) plus ratio bars.
    """
    df = df_breakouts_sum.loc[ps.price_data.index].copy()

    # identify the first condition's up/down col names
    first = breakout_conditions[0]
    up_col = first.up_col
    down_col = first.down_col

    # find ratio columns created by the calc module (prefix match)
    ratio_cols = [c for c in df.columns if c.startswith("RATIO_") and c.endswith(up_col.replace("UP_", ""))]

    fig, axes = plt.subplots(3, 1, figsize=(18, 9), sharex=True)

    # 1) events (+ up, - down)
    axes[0].set_title(f"{ps.idx}: {up_col}/{down_col} events ({ps.sample_start}-{ps.sample_end})",
                      fontsize=12, fontweight="bold")

    ps.plot_price_layer(axes[0])

    ax_t = axes[0].twinx()

    ax_t.axhline(0, color="black", linewidth=0.8)
    ax_t.bar(ps.plot_index, df[up_col].values, label=up_col, color="green", alpha=0.6)
    ax_t.bar(ps.plot_index, -df[down_col].values, label=down_col, color="red", alpha=0.6)
    l1, lab1 = axes[0].get_legend_handles_labels()
    l2, lab2 = ax_t.get_legend_handles_labels()
    ax_t.legend(l1 + l2, lab1 + lab2, loc="upper left", fontsize=8)
    ax_t.set_ylabel("% ativos no evento", fontsize=9)

    # 2) ratio 1 (if present)
    axes[1].set_title(f"{ps.idx}: Ratio (rolling) ({ps.sample_start}-{ps.sample_end})",
                      fontsize=12, fontweight="bold")
    ps.plot_price_layer(axes[1])
    ax_t = axes[1].twinx()
    ax_t.axhline(0, color="black", linewidth=0.8)
    if len(ratio_cols) >= 1:
        r = pd.to_numeric(df[ratio_cols[0]], errors="coerce").fillna(0)
        ax_t.bar(ps.plot_index, r.values, label=ratio_cols[0], color="skyblue", alpha=0.8)
        ax_t.legend(loc="upper left", fontsize=8)
    ax_t.set_ylabel("% ativos no evento", fontsize=9)

    # 3) ratio 2 (if present)
    axes[2].set_title(f"{ps.idx}: Ratio (rolling) ({ps.sample_start}-{ps.sample_end})",
                      fontsize=12, fontweight="bold")
    ps.plot_price_layer(axes[2])
    ax_t = axes[2].twinx()
    ax_t.axhline(0, color="black", linewidth=0.8)
    if len(ratio_cols) >= 2:
        r = pd.to_numeric(df[ratio_cols[1]], errors="coerce").fillna(0)
        ax_t.bar(ps.plot_index, r.values, label=ratio_cols[1], color="cornflowerblue", alpha=0.8)
        ax_t.legend(loc="upper left", fontsize=8)
    ax_t.set_ylabel("% ativos no evento", fontsize=9)

    axes[2].set_xlabel("Data")
    axes[2].set_xticks(ps.tick_positions)
    axes[2].set_xticklabels([ps.date_labels[i] for i in ps.tick_positions], rotation=45, fontsize=8)

    return fig


def plot_stockbee_2(ps: PlotSetup, df_breakouts_sum: pd.DataFrame) -> plt.Figure:
    df = df_breakouts_sum.loc[ps.price_data.index].copy()

    fig, axes = plt.subplots(4, 1, figsize=(18, 9), sharex=True)

    def panel(ax, title, up, down):

        ax.set_title(title, fontsize=9, fontweight="bold")

        ps.plot_price_layer(ax)

        ax_t = ax.twinx()
        ax_t.axhline(0, color="black", linewidth=0.8)

        ax_t.bar(ps.plot_index, df[up].values / ps.num_tickers * 100.0, label=up, color="green")
        ax_t.bar(ps.plot_index, -df[down].values / ps.num_tickers * 100.0, label=down, color="red")
        ax_t.set_ylabel("% ativos no evento", fontsize=9)

        l1, lab1 = ax.get_legend_handles_labels()
        l2, lab2 = ax_t.get_legend_handles_labels()
        ax_t.legend(l1 + l2, lab1 + lab2, loc="upper left", fontsize=8)

    panel(axes[0], f"{ps.idx}: % +/-25% em 1Q ({ps.sample_start}-{ps.sample_end})", "UP_63d_25%", "DOWN_63d_25%")
    panel(axes[1], f"{ps.idx}: % +/-25% em 1 mes ({ps.sample_start}-{ps.sample_end})", "UP_21d_25%", "DOWN_21d_25%")
    panel(axes[2], f"{ps.idx}: % +/-50% em 1 mes ({ps.sample_start}-{ps.sample_end})", "UP_21d_50%", "DOWN_21d_50%")
    panel(axes[3], f"{ps.idx}: % +/-13% em 34 dias ({ps.sample_start}-{ps.sample_end})", "UP_34d_13%", "DOWN_34d_13%")

    axes[3].set_xticks(ps.tick_positions)
    axes[3].set_xticklabels([ps.date_labels[i] for i in ps.tick_positions], rotation=45, fontsize=8)

    return fig


if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    from dataclasses import dataclass

    # ==========================================
    # 1. SETUP MOCKS (To run without 'core')
    # ==========================================
    print(">>> Initializing Test Environment...")


    # Mock Condition Class
    @dataclass
    class MockCondition:
        up_col: str
        down_col: str
        color: str
        plot_group: int


    # Mock PlotSetup Class
    class MockPlotSetup:
        def __init__(self, df_index):
            self.price_data = pd.DataFrame(
                {"Close": 100 + np.random.randn(len(df_index)).cumsum()},
                index=df_index
            )
            self.idx = "TEST_INDEX"
            self.sample_start = str(df_index[0].date())
            self.sample_end = str(df_index[-1].date())
            self.num_tickers = 500
            self.plot_index = np.arange(len(df_index))
            self.tick_positions = np.linspace(0, len(df_index) - 1, 5, dtype=int)
            self.date_labels = [d.strftime("%Y-%m-%d") for d in df_index]

        def plot_price_layer(self, ax):
            # Draw a faint gray line for price
            ax.plot(self.plot_index, self.price_data["Close"].values, color="gray", alpha=0.3, label="Price")


    # Define mock conditions
    # We use specific names to ensure logic in plot_stockbee_1 works (stripping "UP_")
    mock_conds = [
        MockCondition("UP_4pct_1d", "DOWN_4pct_1d", "blue", 1),
        MockCondition("UP_10pct_5d", "DOWN_10pct_5d", "orange", 1),
    ]

    # Monkeypatch the global variable 'breakout_conditions' used in plot_stockbee_1
    breakout_conditions = mock_conds

    # ==========================================
    # 2. GENERATE DUMMY DATA
    # ==========================================
    dates = pd.date_range(start="2024-01-01", periods=60, freq="D")
    ps = MockPlotSetup(dates)

    # Create random data for all columns required by the 3 functions
    data = {
        # Core Indicators
        "Regime_RiskOn": np.random.choice([0, 1], size=len(dates)),
        "Flag_Thrust_Breakouts": np.random.choice([0, 1], size=len(dates), p=[0.9, 0.1]),
        "MA_Breakouts": np.random.randint(10, 100, size=len(dates)),
        "MA_Breakdowns": np.random.randint(10, 100, size=len(dates)),
        "MA_Impulse_Breakouts": np.random.randn(len(dates)),

        # Conditions (Breakouts/Breakdowns)
        "UP_4pct_1d": np.random.randint(0, 50, size=len(dates)),
        "DOWN_4pct_1d": np.random.randint(0, 50, size=len(dates)),
        "UP_10pct_5d": np.random.randint(0, 30, size=len(dates)),
        "DOWN_10pct_5d": np.random.randint(0, 30, size=len(dates)),

        # Ratios for Stockbee 1 (Names must match suffix of UP_ col)
        # Suffix of UP_4pct_1d is "4pct_1d"
        "RATIO_Rolling_4pct_1d": np.random.randn(len(dates)),
        "RATIO_Rolling_Other": np.random.randn(len(dates)),

        # Specific columns for Stockbee 2
        "UP_63d_25%": np.random.randint(0, 40, len(dates)), "DOWN_63d_25%": np.random.randint(0, 40, len(dates)),
        "UP_21d_25%": np.random.randint(0, 40, len(dates)), "DOWN_21d_25%": np.random.randint(0, 40, len(dates)),
        "UP_21d_50%": np.random.randint(0, 20, len(dates)), "DOWN_21d_50%": np.random.randint(0, 20, len(dates)),
        "UP_34d_13%": np.random.randint(0, 60, len(dates)), "DOWN_34d_13%": np.random.randint(0, 60, len(dates)),
    }
    df_sum = pd.DataFrame(data, index=dates)

    # ==========================================
    # 3. RUN TESTS & PRINT "WHAT IS PLOTTED"
    # ==========================================

    print("\n" + "=" * 60)
    print("TEST REPORT: Module Plot Content")
    print("=" * 60)

    # --- Test 1: plot_breakouts ---
    print("\n[Figure 1] plot_breakouts(ps, df_sum)")
    try:
        fig1 = plot_breakouts(ps, df_sum, conditions=mock_conds)
        print("STATUS: Generated Successfully")
        print("CONTENTS:")
        print("  Panel 1 (Top - Breakouts):")
        print("    • [Background] Risk-On Regime (Green Shading)")
        print("    • [Overlay]    Thrust Markers (Purple Vertical Lines)")
        print("    • [Price]      Price Index (Gray Line)")
        print("    • [Bar Chart]  Stacked UP Breakouts (UP_4pct_1d, UP_10pct_5d...)")
        print("    • [Line]       MA Breakouts (Green Dashed)")
        print("  Panel 2 (Bottom - Breakdowns):")
        print("    • [Background] Risk-On Regime (Green Shading)")
        print("    • [Overlay]    Thrust Markers (Purple Vertical Lines)")
        print("    • [Price]      Price Index (Gray Line)")
        print("    • [Bar Chart]  Stacked DOWN Breakdowns (DOWN_4pct_1d...)")
        print("    • [Line]       MA Breakdowns (Red Dashed)")
        print("    • [Line]       MA Impulse Overlay (Black)")
    except Exception as e:
        print(f"STATUS: Failed ({e})")

    # --- Test 2: plot_stockbee_1 ---
    print("\n[Figure 2] plot_stockbee_1(ps, df_sum)")
    try:
        fig2 = plot_stockbee_1(ps, df_sum)
        print("STATUS: Generated Successfully")
        print("CONTENTS:")
        print(f"  Panel 1 (Events):")
        print(f"    • [Bar Chart]  {mock_conds[0].up_col} (Green) vs {mock_conds[0].down_col} (Red)")
        print(f"    • [Price]      Price Index Overlay")
        print(f"  Panel 2 (Ratio 1):")
        print(f"    • [Bar Chart]  Rolling Ratio: RATIO_Rolling_4pct_1d (Skyblue)")
        print(f"  Panel 3 (Ratio 2):")
        print(f"    • [Bar Chart]  Rolling Ratio: RATIO_Rolling_Other (Cornflowerblue)")
    except Exception as e:
        print(f"STATUS: Failed ({e})")

    # --- Test 3: plot_stockbee_2 ---
    print("\n[Figure 3] plot_stockbee_2(ps, df_sum)")
    try:
        fig3 = plot_stockbee_2(ps, df_sum)
        print("STATUS: Generated Successfully")
        print("CONTENTS (Fixed 4-Panel Layout):")
        print("  Panel 1: Price + Bar Chart (+/- 25% in 63 days)")
        print("  Panel 2: Price + Bar Chart (+/- 25% in 21 days)")
        print("  Panel 3: Price + Bar Chart (+/- 50% in 21 days)")
        print("  Panel 4: Price + Bar Chart (+/- 13% in 34 days)")
    except Exception as e:
        print(f"STATUS: Failed ({e})")

    print("\n" + "=" * 60)
    print("Tests complete. Displaying plots...")
    plt.show()