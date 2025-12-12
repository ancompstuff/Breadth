import pandas as pd
import numpy as np

def detect_dispersion_patterns(df_idx: pd.DataFrame,
                               vwma_periods: list,
                               abs_prefix: str = "Abs_C-VWMA") -> pd.DataFrame:
    """
    Detects 3 high-value compression/dispersion patterns:

    1) Sequential Cascade         (5→12→25→40→80→100→200)
    2) All-rows Detonation        (all VWMA rows bright simultaneously)
    3) Compression Squeeze        (all VWMA rows extremely dark)

    INPUTS:
        df_idx:          Index-level compression DataFrame
        vwma_periods:    List of VWMA periods used (e.g. [5,12,25,40,80,100,200])
        abs_prefix:      The prefix for abs compression columns

    OUTPUT:
        df with 3 new boolean columns
    """

    df = df_idx.copy()

    # -----------------------------
    # Extract rows for all VWMA periods
    # -----------------------------
    comp_cols = [f"{abs_prefix}{ma}" for ma in vwma_periods if f"{abs_prefix}{ma}" in df.columns]
    comp = df[comp_cols]

    # Normalize each row → 0 to 1 (heatmap normalization)
    comp_norm = (comp - comp.min()) / (comp.max() - comp.min() + 1e-9)

    # Store thresholds
    HIGH = 0.75
    LOW = 0.25

    # Output signals
    df["AllRowsDetonation"] = (comp_norm > HIGH).all(axis=1).astype(int)
    df["CompressionSqueeze"] = (comp_norm < LOW).all(axis=1).astype(int)

    # --------------------------------------
    # Sequential Cascade detection logic
    # --------------------------------------
    # Order by increasing VWMA horizon
    sorted_cols = list(comp_norm.columns)

    # Bright when >HIGH
    bright = (comp_norm > HIGH).astype(int)

    # Check if the bright pattern appears in exact order:
    # row[i] <= row[i+1] meaning brightness propagates outward
    seq = []
    for i in range(len(bright)):
        row = bright.iloc[i].values
        # row must be non-decreasing in brightness along the sequence
        if np.all(row[:-1] <= row[1:]):
            seq.append(1)
        else:
            seq.append(0)

    df["SequentialCascade"] = seq

    return df
