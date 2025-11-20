import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Data loading (new architecture)
from data.loader import load_market

# Indicators
from indicators.moving_averages import calculate_mas
from indicators.volume import volume_indicators
from indicators.highs_lows import compute_highs_lows
from indicators.breadth import calculate_breadth
from indicators.compression import calculate_compression
from indicators.run_length import compute_run_length
from indicators.rsi import calculate_rsi
from indicators.breakout import breakout_indicators
from indicators.breakout_readiness import compute_breakout_readiness
from indicators.breakout_score import compute_breakout_score
from indicators.williams import williams_indicators

# Plotting
from plotting.setup import make_setup
from plotting.index_vs_ma import plot_index_vs_ma
from plotting.volume_plots import plot_volume
from plotting.highs_lows_plots import plot_highs_lows
from plotting.breadth_plots import plot_breadth
from plotting.compression_plots import plot_compression
from plotting.runlength_plots import plot_up_down_days
from plotting.rsi_plots import plot_rsi
from plotting.breakout_plots import (
    plot_breakouts,
    plot_stockbee_1,
    plot_stockbee_2,
)
from plotting.williams_plots import plot_williams
from plotting.breakout_readiness_plots import plot_brs
from plotting.breakout_score_plots import plot_score


#############################################
#--------------- MAIN -----------------------#
#############################################

def main():

    # ---------------------------------------------------
    # Load all data into a structured MarketData object
    # ---------------------------------------------------
    market = load_market()        # index_df, eod_df, config
    setup = make_setup(market)    # handles x-axis, lookback, labels, etc.

    # Output file
    pdf_filename = f"{market.config['idx_code']}_{datetime.today().strftime('%Y-%m-%d')}.pdf"
    pdf_path = os.path.join(market.config["pdf_folder"], pdf_filename)

    with PdfPages(pdf_path) as pdf:

        # -------------------------------
        # Volume
        # -------------------------------
        vol = volume_indicators(market)
        fig = plot_volume(vol, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Moving averages (MA, VWMA)
        # -------------------------------
        ma = calculate_mas(market)

        fig = plot_index_vs_ma(ma, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # MA breadth
        breath = calculate_breadth(market, ma)
        fig = plot_breadth(breath, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # Compression / expansion
        compress = calculate_compression(market, ma)
        fig = plot_compression(compress, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Highs and lows
        # -------------------------------
        hl = compute_highs_lows(market)
        fig = plot_highs_lows(hl, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Advance/Decline (breadth)
        # Already handled above
        # -------------------------------

        # -------------------------------
        # Run Lengths
        # -------------------------------
        rl = compute_run_length(market)
        fig1, fig2 = plot_up_down_days(rl, setup)
        pdf.savefig(fig1); plt.close(fig1)
        pdf.savefig(fig2); plt.close(fig2)

        # -------------------------------
        # RSI / Momentum
        # -------------------------------
        rsi = calculate_rsi(market)
        fig = plot_rsi(rsi, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Breakouts
        # -------------------------------
        b = breakout_indicators(market)
        fig = plot_breakouts(b, setup)
        pdf.savefig(fig); plt.close(fig)

        fig = plot_stockbee_1(b, setup)
        pdf.savefig(fig); plt.close(fig)

        fig = plot_stockbee_2(b, setup)
        pdf.savefig(fig); plt.close(fig)

        # -------------------------------
        # Williams %R studies
        # -------------------------------
        w = williams_indicators(market)
        fig = plot_williams(w, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Breakout readiness
        # -------------------------------
        brs = compute_breakout_readiness(market)
        fig = plot_brs(brs, setup)
        pdf.savefig(fig)
        plt.close(fig)

        # -------------------------------
        # Breakout score
        # -------------------------------
        score = compute_breakout_score(market)
        fig = plot_score(score, setup)
        pdf.savefig(fig)
        plt.close(fig)

    # -----------------------------------
    # Open PDF automatically if possible
    # -----------------------------------
    if os.path.exists(pdf_path):
        try:
            os.startfile(pdf_path)
        except AttributeError:
            os.system(f'open "{pdf_path}"')
    else:
        print("PDF not generated: ", pdf_path)


if __name__ == "__main__":
    main()
