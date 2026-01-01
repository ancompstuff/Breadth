import pandas as pd
import numpy as np
import talib


def compute_zbt_thrust(
    zbt: pd.Series,
    lookback: int = 10,
    lower: float = 0.40,
    upper: float = 0.615
) -> pd.Series:
    """
    Compute Zweig Breadth Thrust regime.

    A thrust occurs when the 10-day EMA of the breadth ratio
    rises from below `lower` to above `upper` within `lookback` days.

    Returns:
        Boolean Series: True while thrust regime is active.
    """
    thrust_trigger = pd.Series(False, index=zbt.index)

    for i in range(len(zbt)):
        if zbt.iloc[i] >= upper:
            start = max(0, i - lookback)
            if (zbt.iloc[start:i] <= lower).any():
                thrust_trigger.iloc[i] = True

    # Extend thrust while ZBT remains above lower bound
    thrust_active = thrust_trigger.copy()
    for i in range(1, len(thrust_active)):
        if thrust_active.iloc[i - 1] and zbt.iloc[i] >= lower:
            thrust_active.iloc[i] = True

    return thrust_active


def calculate_advance_decline(df_idx: pd.DataFrame, df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate advance/decline indicators including:
    TRIN, cumulative A/D, McClellan Oscillator,
    McClellan Summation Index (MSI),
    Zweig Breadth Thrust (ZBT) and ZBT thrust regime.
    """

    # Number of tickers
    num_stocks = df_comp.columns.get_level_values(1).nunique()

    # Daily price direction
    price_change = df_comp['Adj Close'].diff()
    price_direction = np.sign(price_change)

    # Advancing / declining issues
    advancing_stocks = (price_direction == 1).sum(axis=1)
    declining_stocks = (price_direction == -1).sum(axis=1)

    # Volumes
    volume = df_comp['Volume']
    advancing_volume = volume.where(price_direction == 1).sum(axis=1)
    declining_volume = volume.where(price_direction == -1).sum(axis=1)

    # TRIN components
    adv_issues = advancing_stocks.replace(0, np.nan)
    dec_issues = declining_stocks.replace(0, np.nan)
    adv_vol = advancing_volume.replace(0, np.nan)
    dec_vol = declining_volume.replace(0, np.nan)

    trin = (adv_issues / dec_issues) / (adv_vol / dec_vol)
    trin.name = "TRIN"

    adv_dec_indicators = pd.DataFrame(
        {
            'Advancing': advancing_stocks,
            'Declining': declining_stocks,
            'TRIN': trin,
            'idx_close': df_idx['Adj Close']
        },
        index=df_idx.index
    )
    #adv_dec_indicators.index = df_idx.index

    # ------------------------------------------------------------
    # Advance / Decline
    # ------------------------------------------------------------
    adv_dec_diff = advancing_stocks - declining_stocks
    adv_dec_indicators['A/D_diff'] = adv_dec_diff
    adv_dec_indicators['A/D_cum_diff'] = adv_dec_diff.cumsum()

    # ------------------------------------------------------------
    # McClellan Oscillator
    # ------------------------------------------------------------
    diff = adv_dec_diff.fillna(0).astype('float64').values

    ema_19 = talib.EMA(diff, timeperiod=19)
    ema_39 = talib.EMA(diff, timeperiod=39)

    adv_dec_indicators['McClellan_Oscillator'] = ema_19 - ema_39

    # ------------------------------------------------------------
    # McClellan Summation Index (MSI)
    # ------------------------------------------------------------
    adv_dec_indicators['McClellan_Summation'] = (
        adv_dec_indicators['McClellan_Oscillator'].cumsum()
    )

    # ------------------------------------------------------------
    # Zweig Breadth Thrust (ZBT)
    # ------------------------------------------------------------
    total_issues = advancing_stocks + declining_stocks
    breadth_ratio = advancing_stocks / total_issues.replace(0, np.nan)

    zbt = breadth_ratio.ewm(span=10, adjust=False).mean()
    adv_dec_indicators['ZBT'] = zbt

    # ZBT thrust regime
    adv_dec_indicators['ZBT_thrust'] = compute_zbt_thrust(zbt)


    return adv_dec_indicators


#################################################################################################################
# --------------------------------------------- TEST ------------------------------------------------------------
#################################################################################################################
import os
import itertools
from pathlib import Path
from tabulate import tabulate


if __name__ == "__main__":
    print(f"{'=' * 30}\nTESTING MODULE: adv_dec_indicators\n{'=' * 30}")


    def print_df_summary(name: str, df: pd.DataFrame):
        print(f"\n>>> DATAFRAME: {name}")
        print(f"    Shape: {df.shape}")
        print(f"    Columns ({len(df.columns)}):")
        # Handle MultiIndex and standard columns for readability
        if isinstance(df.columns, pd.MultiIndex):
            cols = [str(c) for c in df.columns.get_level_values(0).unique().tolist()]
        else:
            cols = [str(c) for c in df.columns.tolist()]

        if len(cols) > 10:
            print(f"      {cols[:5]} ... {cols[-5:]}")
        else:
            print(f"      {cols}")


    # 1. Setup paths to the data_cache
    # Moves up from /indicators/ to root, then into data_cache
    data_dir = Path(__file__).resolve().parent.parent / "data_cache"
    index_path = data_dir / "index_df.parquet"
    comp_path = data_dir / "components_df.parquet"

    if not index_path.exists() or not comp_path.exists():
        print(f"ERROR: Cached data not found at {data_dir}. Run main.py first.")
    else:
        # 2. Load the cached data
        df_idx = pd.read_parquet(index_path)
        df_comp = pd.read_parquet(comp_path)
        print(f"Successfully loaded Index data with {len(df_idx)} rows.")

        # 3. Test primary function
        df_adv_dec = calculate_advance_decline(df_idx, df_comp)
        print_df_summary("Advance/Decline Indicators", df_adv_dec)

        # 4. Prepare Table of Resulting Columns
        # Extract Level 0 labels for the table (single-level for this module)
        result_cols = df_adv_dec.columns.tolist()

        # Create a formatted table display
        # We split the long list into two columns for better table formatting
        mid = (len(result_cols) + 1) // 2
        col1 = result_cols[:mid]
        col2 = result_cols[mid:]

        table_data = list(itertools.zip_longest(col1, col2, fillvalue=""))

        print("\n>>> Indicators Generated by calculate_advance_decline")
        print(tabulate(
            table_data,
            headers=["Category / Indicator (Part 1)", "Category / Indicator (Part 2)"],
            tablefmt="grid"
        ))

        # 5. Quick check on the ZBT Series specifically
        print(f"\n>>> ZBT Thrust Regime Sample (Last 5 days):")
        print(df_adv_dec['ZBT_thrust'].tail(5))

    print(f"\n{'=' * 30}\nTEST COMPLETED\n{'=' * 30}")
