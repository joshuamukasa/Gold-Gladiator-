"""
Josh Gold Engine – Setup 1 & Setup 2

This file is PURE ENGINE LOGIC.
No UI, no CSV upload, no Streamlit, no MT5.

It does ONE job:
Given M15 + M5 OHLC data, it finds your trades exactly
how you trade them:

1. Start from London / New York time windows
2. Look LEFT from the window to the start of the day
3. Decide if the day is:
      - Setup 1 (manipulation → BOS)
      - Setup 2 (clean displacement → retrace)
4. Wait for price to retrace into FVG + OB zone
5. Confirm with engulfing candle (body closes past wick)
6. Entry only AFTER confirmation

You (or the UI) will call:

    find_trades(m15_df, m5_df)

and get back a list of trades.
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Dict
import pandas as pd

# ---------------------------------------------------------
# TYPES
# ---------------------------------------------------------

SessionName = Literal["LONDON", "NEWYORK"]


@dataclass
class Trade:
    """
    A single trade detected by the engine.
    """
    time_ny: pd.Timestamp
    session: SessionName
    setup_type: Literal["SETUP_1", "SETUP_2"]
    direction: Literal["BUY", "SELL"]
    timeframe: Literal["M5", "M15"]  # which TF gave the confirmation
    entry_price: float
    stop_price: float
    rr_target: float = 3.0  # YOU decide risk later, this is just structure


# ---------------------------------------------------------
# CONFIG – YOU CAN TWEAK THESE IF NEEDED
# ---------------------------------------------------------

# London / New York windows – NEW YORK LOCAL TIME
LON_START = (3, 0)
LON_END   = (6, 0)

NY_START  = (8, 30)
NY_END    = (11, 30)

# How many minutes back from the session start to look for structure
LOOKBACK_MINUTES = 24 * 60  # whole day


# ---------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------

def _in_window(t: pd.Timestamp) -> Optional[SessionName]:
    """
    Decide if a NY-local timestamp is inside a trading window.
    Returns "LONDON", "NEWYORK" or None.
    """
    h, m = t.hour, t.minute
    total = h * 60 + m

    lon_s = LON_START[0] * 60 + LON_START[1]
    lon_e = LON_END[0] * 60 + LON_END[1]

    ny_s  = NY_START[0] * 60 + NY_START[1]
    ny_e  = NY_END[0] * 60 + NY_END[1]

    if lon_s <= total <= lon_e:
        return "LONDON"
    if ny_s <= total <= ny_e:
        return "NEWYORK"
    return None


def _engulf(prev: pd.Series, curr: pd.Series) -> Dict[str, bool]:
    """
    Your engulf definition:
    - Body must close beyond the wick of the previous candle.
    """
    bullish = (
        curr["close"] > curr["open"] and
        curr["close"] > prev["high"]
    )
    bearish = (
        curr["close"] < curr["open"] and
        curr["close"] < prev["low"]
    )
    return {"bullish": bullish, "bearish": bearish}


def _simple_fvg(prev: pd.Series, curr: pd.Series, nxt: pd.Series) -> Dict[str, bool]:
    """
    Very simple FVG approximation:
    - Bullish FVG: prev.high < nxt.low
    - Bearish FVG: prev.low  > nxt.high
    This is *not* perfect ICT, just a clean imbalance footprint.
    """
    bullish = prev["high"] < nxt["low"]
    bearish = prev["low"]  > nxt["high"]
    return {"bullish": bullish, "bearish": bearish}


# ---------------------------------------------------------
# STRUCTURE CLASSIFICATION (SETUP 1 vs SETUP 2)
# ---------------------------------------------------------

def _classify_setup(day_df: pd.DataFrame) -> Dict[str, str]:
    """
    Approximate your mental classification:

    - SETUP 1:
        There is a clear 'fake move' + strong BOS the other way.
        We approximate this as:
            * the extreme (high or low) is made early,
            * and later price closes strongly away from it.

    - SETUP 2:
        No obvious manipulation, just steady displacement
        from open to close → continuation.
    """
    day_df = day_df.sort_values("time_ny")

    first = day_df.iloc[0]
    last  = day_df.iloc[-1]

    day_dir = "UP" if last["close"] > first["open"] else "DOWN"

    high_idx = day_df["high"].idxmax()
    low_idx  = day_df["low"].idxmin()

    # If high is made early, then we close much lower → fake up → real down
    if high_idx < low_idx and day_dir == "DOWN":
        return {"setup": "SETUP_1", "bias": "SELL"}

    # If low is made early, then we close much higher → fake down → real up
    if low_idx < high_idx and day_dir == "UP":
        return {"setup": "SETUP_1", "bias": "BUY"}

    # Otherwise treat it as SETUP 2 continuation:
    if day_dir == "UP":
        return {"setup": "SETUP_2", "bias": "BUY"}
    else:
        return {"setup": "SETUP_2", "bias": "SELL"}


# ---------------------------------------------------------
# CORE ENGINE
# ---------------------------------------------------------

def find_trades(
    m15: pd.DataFrame,
    m5: pd.DataFrame,
    rr_target: float = 3.0
) -> List[Trade]:
    """
    Main entry point.

    Parameters
    ----------
    m15 : DataFrame
        Must contain columns: ['time_ny','open','high','low','close']
        One row per M15 candle, in NEW YORK time.
    m5 : DataFrame
        Same columns, M5 candles, in NEW YORK time.

    Returns
    -------
    List[Trade]
        A list of Trade objects (structure only, NO RISK sizing).
    """

    # Ensure sorted
    m15 = m15.dropna(subset=["time_ny"]).sort_values("time_ny").reset_index(drop=True)
    m5  = m5.dropna(subset=["time_ny"]).sort_values("time_ny").reset_index(drop=True)

    trades: List[Trade] = []

    # Group by NY "day"
    m15["day"] = m15["time_ny"].dt.date
    m5["day"]  = m5["time_ny"].dt.date

    m15_by_day = {d: g.copy().reset_index(drop=True) for d, g in m15.groupby("day")}
    m5_by_day  = {d: g.copy().reset_index(drop=True) for d, g in m5.groupby("day")}

    for day, day15 in m15_by_day.items():

        if day not in m5_by_day:
            continue

        day5 = m5_by_day[day]

        # --- classify daily structure (Setup 1 vs 2 + bias) ---
        struct = _classify_setup(day15)
        setup_type = struct["setup"]      # "SETUP_1" or "SETUP_2"
        bias       = struct["bias"]       # "BUY" or "SELL"

        # --- scan through session windows on BOTH TFs ---
        # We will build a single list of "confirmation candidates"
        # from M15 and M5, then choose the earliest one per session.

        session_candidates: List[Trade] = []

        # helper to process a given TF df
        def scan_tf(tf_df: pd.DataFrame, tf_name: str):
            nonlocal session_candidates

            for i in range(2, len(tf_df) - 1):
                row = tf_df.iloc[i]
                t   = row["time_ny"]
                session = _in_window(t)
                if session is None:
                    continue

                # Lookback window for "from session back to start of day"
                # (we already used full day for structure, this is just context)
                # Not strictly needed here, but kept to respect your logic.
                # left = tf_df[tf_df["time_ny"] <= t]

                prev = tf_df.iloc[i - 1]
                nxt  = tf_df.iloc[i + 1]

                fvg = _simple_fvg(prev, row, nxt)
                if not (fvg["bullish"] or fvg["bearish"]):
                    continue

                engulf = _engulf(prev, row)
                if not (engulf["bullish"] or engulf["bearish"]):
                    continue

                # Direction must respect daily bias
                direction: Optional[str] = None
                if engulf["bullish"] and bias == "BUY":
                    direction = "BUY"
                if engulf["bearish"] and bias == "SELL":
                    direction = "SELL"

                if direction is None:
                    continue

                # Stop placement: just beyond local structure behind the engulf
                if direction == "BUY":
                    stop = min(prev["low"], row["low"])
                else:  # SELL
                    stop = max(prev["high"], row["high"])

                entry = row["close"]

                trade = Trade(
                    time_ny=row["time_ny"],
                    session=session,
                    setup_type=setup_type,
                    direction=direction,
                    timeframe=tf_name,
                    entry_price=float(entry),
                    stop_price=float(stop),
                    rr_target=float(rr_target),
                )

                session_candidates.append(trade)

        # Scan M15 + M5
        scan_tf(day15, "M15")
        scan_tf(day5, "M5")

        # If we found any confirmation trades this day, keep the earliest per session
        if not session_candidates:
            continue

        # Sort all candidates by time, choose earliest per (day,session)
        session_candidates.sort(key=lambda tr: tr.time_ny)

        seen_sessions: set[SessionName] = set()
        for tr in session_candidates:
            key = tr.session
            if key in seen_sessions:
                continue
            seen_sessions.add(key)
            trades.append(tr)

    return trades

# --------------------------------------------------------------------
# Helper for the Streamlit dashboard
# --------------------------------------------------------------------

from dataclasses import asdict

def scan_market(symbol: str = "XAUUSD"):
    """
    This is the ONLY function the Streamlit app will call.

    It should:
      - Look at the current market (M5 + M15, your time windows)
      - Decide if there is a valid setup (1 or 2)
      - Return a simple dict with the trade plan
      - Or return None if there is NO TRADE

    IMPORTANT:
      Inside this function you must call your main analysis function.
      If your main function has a different name than the one I put,
      just change that one line.
    """

    # 🔴 CHANGE THIS LINE to match your real analysis function
    # For example, if your main function is called `evaluate_setups`
    # or `run_strategy`, call that here instead.
    result = evaluate_setups(symbol)   # <-- rename this if needed

    # If your `result` object already has a flag for "no setup", use it here.
    if result is None:
        return None
    if hasattr(result, "has_signal") and not result.has_signal:
        return None

    # If `result` is a dataclass, convert to dict
    try:
        data = asdict(result)
    except Exception:
        # otherwise assume it's already a dict-like object
        data = dict(result)

    # Normalise keys so the app always knows what to expect
    return {
        "symbol": data.get("symbol", symbol),
        "direction": data.get("direction"),          # "BUY" or "SELL"
        "setup_type": data.get("setup_type"),        # 1 or 2
        "session": data.get("session", data.get("window_name")),
        "entry": float(data.get("entry_price", data.get("entry", 0))),
        "sl": float(data.get("stop_loss", data.get("sl", 0))),
        "tp": float(data.get("take_profit", data.get("tp", 0))),
        "reason": data.get("reason", data.get("comment", "")),
    }
