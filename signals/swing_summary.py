import matplotlib.pyplot as plt


def print_and_plot_summary_page(indicators, swing_metrics, ps):
    """
    Evaluates latest indicators, prints summary to terminal, and
    returns a Matplotlib Figure to be appended as the 4th page of your PDF.
    """
    latest_date = ps.index[-1].strftime('%Y-%m-%d')

    # Extract latest values
    comp_squeeze = indicators["agg_ttm_squeeze"]["comp_squeeze_pct"].iloc[-1]
    vc_ratio = indicators["agg_ttm_squeeze"]["vc_ratio"].iloc[-1]
    ttm_mom = indicators["agg_ttm_squeeze"]["ttm_momentum"].iloc[-1]

    up4 = swing_metrics["stockbee_up4"].iloc[-1]
    down4 = swing_metrics["stockbee_down4"].iloc[-1]
    net_4pct = swing_metrics["net_stockbee_4pct"].iloc[-1]

    pct_10ma = swing_metrics["pct_above_10ma"].iloc[-1]
    pct_50ma = swing_metrics["pct_above_50ma"].iloc[-1]

    # Determine Market State and Daytrading Bias
    if net_4pct >= 15 and pct_10ma > pct_50ma and ttm_mom > 0:
        regime = "BULLISH IGNITION / RISK ON"
        winfut_bias = "LONG BIAS (Buy Dips / Opening Drive Longs)"
        color = "green"
    elif net_4pct <= -15 or (pct_10ma < 20 and ttm_mom < 0):
        regime = "BEARISH EXPANSION / RISK OFF"
        winfut_bias = "SHORT BIAS (Short Rallies / Breakdown Follow-through)"
        color = "red"
    elif comp_squeeze > 50:
        regime = "HIGH COMPRESSION (Squeeze Loading)"
        winfut_bias = "NEUTRAL / MEAN REVERSION (Range-Bound Rotations)"
        color = "orange"
    else:
        regime = "NEUTRAL / CONSOLIDATION"
        winfut_bias = "NEUTRAL (Trade Level-to-Level, Scalp Both Sides)"
        color = "gray"

    # Terminal Output
    print("\n" + "=" * 60)
    print(f"   SWING TRADING & DAYTRADING BIAS REPORT | {latest_date}")
    print("=" * 60)
    print(f" Market State: {regime}")
    print(f" WINFUT Bias : {winfut_bias}")
    print("-" * 60)
    print(f" Stockbee +4% Movers : +{up4} | -4% Movers: -{down4} (Net: {net_4pct:+d})")
    print(f" Market Participation: {pct_10ma:.1f}% > 10MA | {pct_50ma:.1f}% > 50MA")
    print(f" Squeeze Metrics     : {comp_squeeze:.1f}% in Squeeze | VC Ratio: {vc_ratio:.2f}")
    print("=" * 60 + "\n")

    # Generate Page 4 Matplotlib Figure
    fig, ax = plt.subplots(figsize=(11.69, 8.27))  # A4 Landscape
    ax.axis('off')

    summary_text = (
        f"DAILY MARKET BREADTH & SWING TRADING SUMMARY\n"
        f"Date: {latest_date}\n\n"
        f"--------------------------------------------------------------------\n"
        f"MARKET REGIME: {regime}\n"
        f"WINFUT DAYTRADING BIAS: {winfut_bias}\n"
        f"--------------------------------------------------------------------\n\n"
        f"1. STOCKBEE EXPANSION METRICS:\n"
        f"   • +4% Breakout Stocks : {up4}\n"
        f"   • -4% Breakdown Stocks: {down4}\n"
        f"   • Net Expansion Score : {net_4pct:+d}\n\n"
        f"2. PARTICIPATION & MA CROSSOVERS:\n"
        f"   • Stocks > 10 MA: {pct_10ma:.1f}%\n"
        f"   • Stocks > 50 MA: {pct_50ma:.1f}%\n"
        f"   • Expansion Status: {'Bullish (10MA > 50MA)' if pct_10ma > pct_50ma else 'Bearish / Neutral'}\n\n"
        f"3. VOLATILITY & SQUEEZE CYCLE:\n"
        f"   • Components in Squeeze: {comp_squeeze:.1f}%\n"
        f"   • Volatility Ratio (VC): {vc_ratio:.2f}\n"
        f"   • Aggregate TTM Momentum: {ttm_mom:.2f}\n"
    )

    ax.text(0.05, 0.90, summary_text, transform=ax.transAxes, fontsize=12,
            family='monospace', verticalalignment='top',
            bbox=dict(boxstyle='round,pad=1', facecolor='whitesmoke', edgecolor=color, linewidth=2))

    plt.tight_layout()
    return fig