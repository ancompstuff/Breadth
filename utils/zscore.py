import pandas as pd
import numpy as np


def rolling_robust_zscore(series: pd.Series,
                          mode: str = "swing",
                          score_params: dict = None) -> pd.Series:
    """
    Rolling robust z-score using median and MAD (L1) with optional clipping.

    How unusual is this data point compared to what's normal?

    Z-Score Range	Interpretation	    Probability
    -1.0 to +1.0	Normal range	    ~68% of data points
    -2.0 to +2.0	Mildly unusual	    ~95% of data points
    Beyond ±2.0	    Very unusual	    ~5% of data points
    Beyond ±3.0	    Extremely unusual	~0.3% of data points

    Parameters
    ----------
    series : pd.Series
        Input time series data
    mode : str
        One of "swing", "longterm", or "anomalies"
    score_params : dict, optional
        Dictionary of parameter sets for different modes
        If None, uses default parameters

    Returns
    -------
    pd.Series
        Rolling robust z-scores
    """
    # Default parameters if not provided
    if score_params is None:
        score_params = {
            "swing": {"window": 20, "min_periods": 10, "clip": 3.5},
            "longterm": {"window": 50, "min_periods": 30, "clip": 4.0},
            "anomalies": {"window": 30, "min_periods": 15, "clip": None}
        }

    # Validate mode
    if mode not in score_params:
        raise ValueError(f"Mode '{mode}' not found in score_params. "
                         f"Available modes: {list(score_params.keys())}")

    # Get parameters for the selected mode
    params = score_params[mode]
    window = params["window"]
    min_periods = params["min_periods"]
    clip = params["clip"]

    # Original robust z-score calculation
    roll_median = series.rolling(window=window, min_periods=min_periods).median()
    # Median Absolute Deviation (MAD): MEDIAN of the absolute deviations from the data's MEDIAN.
    # Original Z-score used rolling mean and standard deviation, which are sensitive to outliers
    # The robust version replaces them with:
    # - Rolling median (center)
    # - Rolling MAD (scale)

    mad = (series - roll_median).abs().rolling(window=window, min_periods=min_periods).median()
    # 1.4826 makes MAD comparable to std under normality
    robust_std = (mad * 1.4826).replace(0, np.nan)
    z = (series - roll_median) / robust_std
    z = z.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if clip is not None:
        z = z.clip(lower=-clip, upper=clip)
    return z