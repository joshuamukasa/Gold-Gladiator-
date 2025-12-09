# strategy_engine.py

import numpy as np
import pandas as pd


def _to_dataframe(rates_array):
    """
    Convert MT5 rates array to a clean pandas DataFrame.
    Expects fields: time, open, high, low, close, tick_volume, spread, real_volume
    """
    if rates_array is None or len(rates_array) == 0:
        return None

    df = pd.DataFrame(rates_array)
    # Ensure required columns exist
    needed = ["time", "open", "high", "low", "close"]
    for col in needed:
        if col not in df.columns:
            return None

    # Convert unix time to pandas datetime if it's numeric
    if np.issubdtype(df["time"].dtype, np.number):
        df["time"] = pd.to_datetime(df["time"], unit="s")

    return df[["time", "open", "high", "low", "close"]]


def _dominant_direction(df):
    """
    Very simple "who is in control" check based on closes.
    This is NOT your full setup logic – just a bias helper.
    """
    if df is None or len(df) < 5:
        return "UNKNOWN"

    first_close = df["close"].iloc[0]
    last_close = df["close"].iloc[-1]

    if last_close > first_close * 1.002:  # >0.2% up
        return "BUY"
    if last_close < first_close * 0.998:  # >0.2% down
        return "SELL"
    return "RANGE"


def analyse_market(rates_m5, rates_m15):
    """
    Main entry point used by the Streamlit app.

    Right now this function:
    - converts raw MT5 rates to DataFrames
    - figures out dominant direction on M15
    - ALWAYS returns NO_TRADE to stay safe until we
      encode your exact Setup 1 / Setup 2 rules.

    Returns a dict, e.g.:

    {
        "has_setup": False,
        "setup_name": None,
        "direction": "BUY" / "SELL" / "RANGE" / "UNKNOWN",
        "timeframe": "M15",
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "explanation": "..."
    }
    """

    df15 = _to_dataframe(rates_m15)
    df5 = _to_dataframe(rates_m5)

    direction = _dominant_direction(df15)

    # 🔒 SAFETY: we don't auto-trade yet – just report bias
    result = {
        "has_setup": False,          # <-- always NO_TRADE for now
        "setup_name": None,
        "direction": direction,
        "timeframe": "M15",
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "explanation": (
            "Pipeline test only – MT5 connection and candle "
            "processing are working. Setup-1 / Setup-2 rules "
            "still need to be fully encoded here."
        ),
        "last_candle_time": df15["time"].iloc[-1] if df15 is not None and len(df15) else None,
    }

    # Later we will replace this block with your real logic:
    # - detect manipulation vs clean move
    # - break of structure
    # - retrace into gap + OB
    # - engulfing confirmation in the correct time window

    return result
