import numpy as np
import pandas as pd

def compute_close_vol_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all indicators needed for the Close/Volume/OBV plot.
    df must contain: ['Adj Close', 'Volume', 'High', 'Low']
    Returns df with new columns added.
    """

    out = df.copy()

    # -------------------
    # OBV (volume * price direction)
    # -------------------
    direction = np.where(out['Adj Close'].diff().fillna(0) > 0, 1, -1)
    out["OBV"] = (direction * out["Volume"] * out["Adj Close"]).cumsum()

    # -------------------
    # Net Money Flow (NMF)
    # -------------------
    typical = (out["High"] + out["Low"] + out["Adj Close"]) / 3
    money_flow = typical * out["Volume"]

    out["Net Money Flow"] = np.where(
        typical.diff() > 0,
        money_flow,
        np.where(typical.diff() < 0, -money_flow, 0)
    )

    out["NMF_cum"] = out["Net Money Flow"].cumsum()

    # -------------------
    # Normalized versions for visualization
    # -------------------
    obv_norm = (out["OBV"] - out["OBV"].min()) / (out["OBV"].max() - out["OBV"].min())
    nmf_norm = (out["NMF_cum"] - out["NMF_cum"].min()) / (out["NMF_cum"].max() - out["NMF_cum"].min())

    # Direction (for bullish/bearish shading)
    obv_ch = obv_norm.diff()
    nmf_ch = nmf_norm.diff()

    out["Bearish"] = ((obv_ch < 0) & (nmf_ch < 0)).astype(int)
    out["Bullish"] = ((obv_ch > 0) & (nmf_ch > 0)).astype(int)

    out["BearStrength"] = (-obv_ch.clip(upper=0)) + (-nmf_ch.clip(upper=0))
    out["BullStrength"] = (obv_ch.clip(lower=0)) + (nmf_ch.clip(lower=0))

    return out


