"""
strategy_engine.py

This file implements Josh's 'Breaking Bad Trades' execution logic
for intraday trading. It does NOT place trades; it only generates
structured trade signals that engine.py can execute.

Expected input: pandas DataFrame `df` with columns:
['time', 'open', 'high', 'low', 'close'] on M5 timeframe,
timestamps already converted to New York time.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import pandas as pd
import numpy as np
from datetime import time as dtime


# --------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------

@dataclass
class TradeSignal:
    time: pd.Timestamp           # time of confirmation candle close
    direction: str               # "buy" or "sell"
    entry: float                 # entry price (engulfing close)
    stop: float                  # stop-loss price
    tp: float                    # take-profit price (first target)
    r_multiple: float            # TP in R (reward/risk)
    session: str                 # "asia" | "london" | "newyork"
    setup_type: str              # "with_manipulation" | "without_manipulation"
    fvg_zone: Tuple[float, float]  # (low, high) of FVG used
    notes: str = ""              # debug / logging notes


# --------------------------------------------------------------------
# Session utilities
# --------------------------------------------------------------------

DEFAULT_SESSION_WINDOWS = {
    "asia":   (dtime(21, 0), dtime(23, 0)),
    "london": (dtime(3, 0),  dtime(5, 0)),
    "newyork":(dtime(8, 0),  dtime(10, 0)),
}


def _in_window(ts: pd.Timestamp,
               start: dtime,
               end: dtime) -> bool:
    """Return True if timestamp `ts` is between start and end (same day, NY)."""
    t = ts.time()
    return (t >= start) and (t <= end)


def _get_session(ts: pd.Timestamp,
                 windows: Dict[str, Tuple[dtime, dtime]]) -> Optional[str]:
    for name, (start, end) in windows.items():
        if _in_window(ts, start, end):
            return name
    return None


# --------------------------------------------------------------------
# Swing & FVG detection
# --------------------------------------------------------------------

def _find_swings(df: pd.DataFrame,
                 lookback: int = 2) -> pd.DataFrame:
    """
    Mark swing highs/lows.
    A swing high: high greater than `lookback` highs on both sides.
    A swing low:  low  lower  than `lookback` lows on both sides.
    """
    highs = df["high"].values
    lows = df["low"].values

    swing_high = np.zeros(len(df), dtype=bool)
    swing_low = np.zeros(len(df), dtype=bool)

    for i in range(lookback, len(df) - lookback):
        if highs[i] == max(highs[i - lookback:i + lookback + 1]):
            swing_high[i] = True
        if lows[i] == min(lows[i - lookback:i + lookback + 1]):
            swing_low[i] = True

    df = df.copy()
    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    return df


def _find_fvgs(df: pd.DataFrame) -> List[Dict]:
    """
    Detect fair value gaps using the classic 3-candle definition.

    Bullish FVG (for buys):
        low[i+1] > high[i-1]  (gap left below price)

    Bearish FVG (for sells):
        high[i+1] < low[i-1]  (gap left above price)
    """
    fvgs = []
    for i in range(1, len(df) - 1):
        h_prev = df["high"].iloc[i - 1]
        l_curr = df["low"].iloc[i]
        h_curr = df["high"].iloc[i]
        l_next = df["low"].iloc[i + 1]

        # bullish gap (price gapped up, leaving gap below)
        if l_curr > h_prev:
            fvgs.append({
                "index": i,
                "type": "bullish",
                "low": h_prev,
                "high": l_curr,
            })

        # bearish gap (price gapped down, leaving gap above)
        if h_curr < l_next:
            fvgs.append({
                "index": i,
                "type": "bearish",
                "low": h_curr,
                "high": l_next,
            })
    return fvgs


def _is_displacement_break(df: pd.DataFrame,
                           i_break: int,
                           direction: str,
                           swing_price: float) -> bool:
    """
    Check that candle at index `i_break` is a displacement candle that
    breaks a swing with its body, not just wick.
    """
    row = df.iloc[i_break]
    open_, close_ = row["open"], row["close"]

    if direction == "up":
        body_high = max(open_, close_)
        return body_high > swing_price
    else:
        body_low = min(open_, close_)
        return body_low < swing_price


# --------------------------------------------------------------------
# Engulfing confirmation
# --------------------------------------------------------------------

def _is_bullish_engulf(prev_c: pd.Series, c: pd.Series) -> bool:
    return (
        c["close"] > c["open"] and           # current is bullish
        prev_c["close"] < prev_c["open"] and # previous is bearish
        c["close"] > max(prev_c["open"], prev_c["close"])  # closes above body
    )


def _is_bearish_engulf(prev_c: pd.Series, c: pd.Series) -> bool:
    return (
        c["close"] < c["open"] and           # current is bearish
        prev_c["close"] > prev_c["open"] and # previous is bullish
        c["close"] < min(prev_c["open"], prev_c["close"])  # closes below body
    )


# --------------------------------------------------------------------
# Main signal generator
# --------------------------------------------------------------------

def generate_signals(
    df: pd.DataFrame,
    risk_per_trade: float = 0.01,
    session_windows: Dict[str, Tuple[dtime, dtime]] = None,
    default_r_multiple: float = 2.0,
) -> List[TradeSignal]:
    """
    Core engine logic:
    - respects execution windows
    - requires manipulation/distribution + swing break
    - requires retrace into FVG+order-block zone
    - requires engulfing confirmation inside window
    """
    if session_windows is None:
        session_windows = DEFAULT_SESSION_WINDOWS

    # 1) prepare structure
    df = df.copy().reset_index(drop=True)
    df = _find_swings(df)
    fvgs = _find_fvgs(df)

    signals: List[TradeSignal] = []

    # 2) iterate candle by candle
    # We'll maintain rolling context for the current day:
    #
    # `bias_direction` : "buy" | "sell" | None
    # `setup_type`     : "with_manipulation" | "without_manipulation" | None
    # `impulse_start_index` : index of candle where displacement leg began
    # `chosen_fvg`     : FVG dict currently in play
    #
    bias_direction = None
    setup_type = None
    impulse_start_index = None
    chosen_fvg = None
    last_session = None

    # Helper to reset daily context (e.g. on new day)
    def reset_context():
        nonlocal bias_direction, setup_type, impulse_start_index, chosen_fvg
        bias_direction = None
        setup_type = None
        impulse_start_index = None
        chosen_fvg = None

    prev_date = df["time"].iloc[0].date()

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1]
        current_date = row["time"].date()

        # New day: reset context
        if current_date != prev_date:
            reset_context()
            prev_date = current_date

        ts = row["time"]
        this_session = _get_session(ts, session_windows)

        # ----------------------------------------------------------------
        # STEP A: Detect bias + impulse leg (manipulation / distribution)
        # ----------------------------------------------------------------

        if bias_direction is None:
            # We look for a strong displacement candle that breaks a swing.
            # For simplicity we use immediate previous swing high/low.
            # Swing high break => bullish bias; swing low break => bearish bias.
            # We also infer setup_type very roughly:
            #   if prior move before break went opposite direction significantly,
            #   treat as "with_manipulation", else "without_manipulation".
            swing_high_idxs = np.where(df["swing_high"].values[:i])[0]
            swing_low_idxs = np.where(df["swing_low"].values[:i])[0]

            # Try bullish break
            if len(swing_high_idxs) > 0:
                last_sh_idx = swing_high_idxs[-1]
                sh_price = df["high"].iloc[last_sh_idx]
                if _is_displacement_break(df, i, "up", sh_price):
                    bias_direction = "buy"
                    impulse_start_index = last_sh_idx
                    # crude manipulation detection: was price generally falling before last_sh_idx?
                    if last_sh_idx >= 5 and df["close"].iloc[last_sh_idx] < df["close"].iloc[last_sh_idx - 5]:
                        setup_type = "with_manipulation"
                    else:
                        setup_type = "without_manipulation"

            # Try bearish break (only if no bullish bias set)
            if bias_direction is None and len(swing_low_idxs) > 0:
                last_sl_idx = swing_low_idxs[-1]
                sl_price = df["low"].iloc[last_sl_idx]
                if _is_displacement_break(df, i, "down", sl_price):
                    bias_direction = "sell"
                    impulse_start_index = last_sl_idx
                    if last_sl_idx >= 5 and df["close"].iloc[last_sl_idx] > df["close"].iloc[last_sl_idx - 5]:
                        setup_type = "with_manipulation"
                    else:
                        setup_type = "without_manipulation"

            # Once bias set, select FVG on that impulse leg
            if bias_direction is not None:
                leg_fvgs = [
                    f for f in fvgs
                    if impulse_start_index <= f["index"] <= i
                    and ((bias_direction == "buy" and f["type"] == "bullish") or
                         (bias_direction == "sell" and f["type"] == "bearish"))
                ]
                if leg_fvgs:
                    # Use the one closest to current price (last one in leg)
                    chosen_fvg = leg_fvgs[-1]

            continue  # move to next candle

        # ----------------------------------------------------------------
        # STEP B: Wait for retrace into chosen FVG zone
        # ----------------------------------------------------------------

        if chosen_fvg is None:
            continue

        f_low, f_high = chosen_fvg["low"], chosen_fvg["high"]

        price_in_fvg = (
            (bias_direction == "buy"  and row["low"] <= f_high and row["low"] >= f_low) or
            (bias_direction == "sell" and row["high"] >= f_low and row["high"] <= f_high)
        )

        # If price has never revisited the zone, keep waiting.
        if not price_in_fvg:
            continue

        # ----------------------------------------------------------------
        # STEP C: Inside FVG and inside execution window → look for engulfing
        # ----------------------------------------------------------------

        if this_session is None:
            continue  # not in time window, ignore confirmations

        prev_c = prev_row
        c = row

        is_bull = _is_bullish_engulf(prev_c, c)
        is_bear = _is_bearish_engulf(prev_c, c)

        if bias_direction == "buy" and not is_bull:
            continue
        if bias_direction == "sell" and not is_bear:
            continue

        # We have a valid engulfing confirmation in time window.
        # ----------------------------------------------------------------
        # STEP D: Build trade parameters
        # ----------------------------------------------------------------

        entry = c["close"]

        # Stop = second swing before confirmation.
        # Approximation: take last 2 swings opposite to trade direction and use the earlier one.
        if bias_direction == "buy":
            swing_indices = np.where(df["swing_low"].values[:i])[0]
            if len(swing_indices) >= 2:
                stop_idx = swing_indices[-2]
            elif len(swing_indices) == 1:
                stop_idx = swing_indices[0]
            else:
                # fallback: use recent low
                stop_idx = max(0, i - 10)
            stop = df["low"].iloc[stop_idx]
        else:
            swing_indices = np.where(df["swing_high"].values[:i])[0]
            if len(swing_indices) >= 2:
                stop_idx = swing_indices[-2]
            elif len(swing_indices) == 1:
                stop_idx = swing_indices[0]
            else:
                stop_idx = max(0, i - 10)
            stop = df["high"].iloc[stop_idx]

        # Basic sanity: avoid zero / negative RR
        if (bias_direction == "buy" and stop >= entry) or (bias_direction == "sell" and stop <= entry):
            # if this happens, something is off; skip this signal
            continue

        # TP: RR multiple of stop distance (you can later replace with explicit FVG / swing targets)
        r_multiple = default_r_multiple
        risk_per_price = abs(entry - stop)
        if bias_direction == "buy":
            tp = entry + r_multiple * risk_per_price
        else:
            tp = entry - r_multiple * risk_per_price

        signal = TradeSignal(
            time=ts,
            direction=bias_direction,
            entry=entry,
            stop=stop,
            tp=tp,
            r_multiple=r_multiple,
            session=this_session,
            setup_type=setup_type or "unknown",
            fvg_zone=(f_low, f_high),
            notes="engulfing confirmation inside execution window",
        )
        signals.append(signal)

        # After one trade per session, you can either:
        #  - reset context (one shot per day), OR
        #  - keep context and allow multiple trades.
        # For safety here we reset so the engine doesn't overtrade.
        last_session = this_session
        reset_context()

    return signals
