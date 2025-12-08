"""
strategy_engine.py

Core execution logic for the Gold Gladiator intraday framework.

This module follows Joshua's rules:

1. Intraday only. Every day is analysed independently.
2. For each trading session window (London / New York):
   - Start at the session window.
   - Look LEFT from the start of the window back to the beginning of that day.
   - Decide whether the dominant move into the window is:
       a) Clean distribution (no obvious fake-out)  -> SETUP 1
       b) Manipulation + break of structure         -> SETUP 2
3. In both setups, entry comes from:
   - Retrace into a fair value gap (FVG) that contains / overlaps an OB zone.
   - Then an engulfing confirmation in the direction of the trade.
   - The engulfing candle MUST be inside the session window.

The engine outputs a list of setups for the UI to display.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Literal, Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd


Direction = Literal["BUY", "SELL"]
SetupType = Literal["SETUP_1_CLEAN_DISTRIBUTION", "SETUP_2_MANIPULATION_BOS"]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Session windows in **New York time** (24h clock)
# Hours are inclusive of start, exclusive of end.
SESSION_WINDOWS = [
    # name       start_hour  end_hour
    ("LONDON",        3,        5),
    ("NEW_YORK",      8,       10),
]

# Minimum move to consider something a "dominant leg" (in points, not pips).
DOMINANT_MOVE_MIN_POINTS = 150  # tune later

# How many candles before the window we scan to classify manipulation vs clean.
PRE_WINDOW_LOOKBACK_CANDLES = 60  # e.g. 60 x M5 = 5 hours

# How close to window start the manipulation low/high must occur (in candles).
MANIPULATION_RECENT_CANDLES = 15

# Minimum size of the impulse after manipulation to call it BOS (points)
MANIPULATION_BOS_MIN_POINTS = 120

# R multiple for targets
DEFAULT_R_MULTIPLE = 3.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class StrategyParams:
    risk_per_trade_pct: float = 1.0
    r_multiple: float = DEFAULT_R_MULTIPLE


@dataclass
class TradeSetup:
    symbol: str
    session_name: str
    setup_type: SetupType
    direction: Direction

    # key price levels
    entry: float
    stop: float
    target: float

    # meta
    timeframe: str
    trade_time: pd.Timestamp
    day: pd.Timestamp  # date of the session (NY)

    # diagnostics / debug
    dominant_move_direction: Direction
    dominant_move_points: float
    classification_notes: str


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _ensure_time_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make sure the dataframe has a DatetimeIndex named 'time'.
    Assumes df has a 'time' column coming from MT5 / CSV.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        if "time" not in df.columns:
            raise ValueError("DataFrame must have a 'time' column with datetimes.")
        df = df.set_index("time")
    if df.index.tz is None:
        # We assume incoming times are already in New York local time
        # (because that's how you visually read them on MT5).
        df.index = df.index.tz_localize("America/New_York")
    else:
        df.index = df.index.tz_convert("America/New_York")
    return df.sort_index()


def _intraday_groups(df: pd.DataFrame) -> Dict[pd.Timestamp, pd.DataFrame]:
    """
    Split dataframe into dict of {date (NY): intraday_df}.
    """
    grouped: Dict[pd.Timestamp, pd.DataFrame] = {}
    for day, day_df in df.groupby(df.index.date):
        day_ts = pd.Timestamp(day).tz_localize("America/New_York")
        grouped[day_ts] = day_df.sort_index()
    return grouped


def _session_slice(day_df: pd.DataFrame, start_hour: int, end_hour: int) -> pd.DataFrame:
    mask = (day_df.index.hour >= start_hour) & (day_df.index.hour < end_hour)
    return day_df.loc[mask]


def _pre_window_slice(day_df: pd.DataFrame, window_df: pd.DataFrame) -> pd.DataFrame:
    if window_df.empty:
        return day_df.iloc[0:0]
    start_time = window_df.index[0]
    return day_df.loc[day_df.index < start_time]


# ---------------------------------------------------------------------------
# Dominant move + manipulation classification
# ---------------------------------------------------------------------------

def _calc_dominant_move(pre_df: pd.DataFrame) -> Tuple[Optional[Direction], float]:
    """
    Determine the dominant move from start of day to window start.
    Returns (direction, points). Direction None if move is too small.
    """
    if pre_df.empty:
        return None, 0.0

    open_price = float(pre_df.iloc[0]["open"])
    last_close = float(pre_df.iloc[-1]["close"])
    diff = last_close - open_price
    points = abs(diff)

    if points < DOMINANT_MOVE_MIN_POINTS:
        return None, points

    direction: Direction = "BUY" if diff > 0 else "SELL"
    return direction, points


def _detect_manipulation_and_bos(
    pre_df: pd.DataFrame,
    dominant_dir: Direction,
) -> Tuple[bool, str]:
    """
    Very simplified detection of:
    - A liquidity grab ("manipulation") against dominant direction very near the window
    - Followed by an impulse in dominant direction (BOS).

    Returns (is_manipulation_setup, notes)
    """
    if pre_df.empty or len(pre_df) < 10:
        return False, "pre-window data too small"

    # Work only with the last N candles before the window
    lookback_df = pre_df.iloc[-PRE_WINDOW_LOOKBACK_CANDLES:]

    highs = lookback_df["high"].values
    lows = lookback_df["low"].values
    closes = lookback_df["close"].values

    if dominant_dir == "BUY":
        # Manipulation should be downside: a sharp low near the end of lookback
        low_idx = int(np.argmin(lows))
        low_price = float(lows[low_idx])
        last_close = float(closes[-1])

        # check it happens near the window
        near_window = low_idx >= len(lookback_df) - MANIPULATION_RECENT_CANDLES

        # impulse up from low to final close
        impulse_points = last_close - low_price

        if near_window and impulse_points * 1.0 >= MANIPULATION_BOS_MIN_POINTS:
            note = (
                f"Detected downside manipulation low at idx {low_idx} -> "
                f"impulse up {impulse_points:.1f} pts into window."
            )
            return True, note
        else:
            return False, (
                "No strong downside manipulation+impulse detected "
                f"(near_window={near_window}, impulse={impulse_points:.1f})"
            )

    else:  # dominant_dir == "SELL"
        high_idx = int(np.argmax(highs))
        high_price = float(highs[high_idx])
        last_close = float(closes[-1])

        near_window = high_idx >= len(lookback_df) - MANIPULATION_RECENT_CANDLES
        impulse_points = high_price - last_close

        if near_window and impulse_points * 1.0 >= MANIPULATION_BOS_MIN_POINTS:
            note = (
                f"Detected upside manipulation high at idx {high_idx} -> "
                f"impulse down {impulse_points:.1f} pts into window."
            )
            return True, note
        else:
            return False, (
                "No strong upside manipulation+impulse detected "
                f"(near_window={near_window}, impulse={impulse_points:.1f})"
            )


# ---------------------------------------------------------------------------
# FVG + engulfing detection (entry logic)
# ---------------------------------------------------------------------------

def _find_recent_fvg_zone(
    pre_df: pd.DataFrame,
    direction: Direction,
) -> Optional[Tuple[float, float]]:
    """
    Find the most recent fair value gap in the direction of the trade
    in the candles BEFORE the session window.

    For BUY:
        low[i+1] > high[i-1] -> bullish FVG zone between high[i-1], low[i+1]
    For SELL:
        low[i-1] > high[i+1] -> bearish FVG zone between high[i+1], low[i-1]

    Returns (zone_low, zone_high) or None.
    """
    if len(pre_df) < 3:
        return None

    highs = pre_df["high"].values
    lows = pre_df["low"].values

    last_idx = len(pre_df) - 1
    # scan from right to left, we want the most recent valid FVG
    for i in range(last_idx - 1, 1, -1):
        if direction == "BUY":
            if lows[i + 1] > highs[i - 1]:
                zone_low = float(highs[i - 1])
                zone_high = float(lows[i + 1])
                return zone_low, zone_high
        else:  # SELL
            if lows[i - 1] > highs[i + 1]:
                zone_low = float(highs[i + 1])
                zone_high = float(lows[i - 1])
                return zone_low, zone_high

    return None


def _engulfing_in_window(
    window_df: pd.DataFrame,
    direction: Direction,
    fvg_zone: Tuple[float, float],
) -> Optional[Tuple[pd.Timestamp, float, float]]:
    """
    Find the first engulfing candle in the session window that:
    - Occurs after price has traded into the FVG zone
    - Engulfs in the trade direction

    Returns (timestamp, entry_price, stop_price) or None.
    """
    if len(window_df) < 2:
        return None

    zone_low, zone_high = fvg_zone
    prev = window_df.iloc[0]
    prev_open = float(prev["open"])
    prev_close = float(prev["close"])

    touched_zone = False

    for idx in range(1, len(window_df)):
        row = window_df.iloc[idx]
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        c = float(row["close"])

        # Has price traded into the FVG zone yet?
        if not touched_zone:
            if direction == "BUY":
                if l <= zone_high and h >= zone_low:
                    touched_zone = True
            else:  # SELL
                if h >= zone_low and l <= zone_high:
                    touched_zone = True

        if not touched_zone:
            prev_open, prev_close = o, c
            continue

        # Check engulfing body relative to previous candle
        body_prev = abs(prev_close - prev_open)
        body_curr = abs(c - o)

        if body_curr < body_prev * 0.7:  # ignore tiny bodies
            prev_open, prev_close = o, c
            continue

        if direction == "BUY":
            bullish_engulf = (c > o) and (c >= prev_open) and (o <= prev_close)
            if bullish_engulf:
                # entry = close, SL below small local swing
                recent_lows = window_df.iloc[max(0, idx - 3): idx + 1]["low"]
                stop = float(recent_lows.min())
                return row.name, c, stop
        else:  # SELL
            bearish_engulf = (c < o) and (c <= prev_open) and (o >= prev_close)
            if bearish_engulf:
                recent_highs = window_df.iloc[max(0, idx - 3): idx + 1]["high"]
                stop = float(recent_highs.max())
                return row.name, c, stop

        prev_open, prev_close = o, c

    return None


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def find_intraday_setups(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    params: Optional[StrategyParams] = None,
) -> List[TradeSetup]:
    """
    Main entry point used by the Streamlit app / execution engine.

    Parameters
    ----------
    df : DataFrame
        Must contain columns: ['time', 'open', 'high', 'low', 'close'].
        Can also already have DatetimeIndex. Times are assumed to be
        broker times that visually correspond to New York for you.
    symbol : str
        Instrument name, e.g. "GOLD".
    timeframe : str
        e.g. "M5" or "M15" – for display only.
    params : StrategyParams
        Risk config and R-multiple.

    Returns
    -------
    List[TradeSetup]
        One object per detected setup.
    """
    if params is None:
        params = StrategyParams()

    df = _ensure_time_index(df)
    day_groups = _intraday_groups(df)

    all_setups: List[TradeSetup] = []

    for day_ts, day_df in day_groups.items():
        # for each intraday session window
        for session_name, start_hour, end_hour in SESSION_WINDOWS:
            window_df = _session_slice(day_df, start_hour, end_hour)
            if window_df.empty:
                continue

            pre_df = _pre_window_slice(day_df, window_df)
            if pre_df.empty:
                continue

            # 1) Determine dominant move from midnight to window start
            dominant_dir, move_points = _calc_dominant_move(pre_df)
            if dominant_dir is None:
                # No clear dominant move -> skip this window
                continue

            # 2) Classify: clean distribution vs manipulation + BOS
            is_manip, notes = _detect_manipulation_and_bos(pre_df, dominant_dir)
            if is_manip:
                setup_type: SetupType = "SETUP_2_MANIPULATION_BOS"
            else:
                setup_type = "SETUP_1_CLEAN_DISTRIBUTION"

            # 3) Find last FVG zone in direction of dominant move
            fvg_zone = _find_recent_fvg_zone(pre_df, dominant_dir)
            if fvg_zone is None:
                # No valid gap -> no trade
                continue

            # 4) Find engulfing confirmation INSIDE the session window
            eng = _engulfing_in_window(window_df, dominant_dir, fvg_zone)
            if eng is None:
                continue

            trade_time, entry, stop = eng

            if dominant_dir == "BUY":
                risk_points = entry - stop
                target = entry + risk_points * params.r_multiple
            else:
                risk_points = stop - entry
                target = entry - risk_points * params.r_multiple

            if risk_points <= 0:
                # should not happen, but guard anyway
                continue

            setup = TradeSetup(
                symbol=symbol,
                session_name=session_name,
                setup_type=setup_type,
                direction=dominant_dir,
                entry=entry,
                stop=stop,
                target=target,
                timeframe=timeframe,
                trade_time=trade_time,
                day=day_ts,
                dominant_move_direction=dominant_dir,
                dominant_move_points=move_points,
                classification_notes=notes,
            )
            all_setups.append(setup)

    return all_setups


def setups_to_dataframe(setups: List[TradeSetup]) -> pd.DataFrame:
    """
    Convenience helper for the UI: convert setups into a nice DataFrame
    for display in the dashboard.
    """
    if not setups:
        return pd.DataFrame(
            columns=[
                "day",
                "time",
                "symbol",
                "session",
                "setup_type",
                "direction",
                "entry",
                "stop",
                "target",
                "dominant_move_direction",
                "dominant_move_points",
                "notes",
            ]
        )

    rows: List[Dict[str, Any]] = []
    for s in setups:
        rows.append(
            {
                "day": s.day.date().isoformat(),
                "time": s.trade_time.strftime("%Y-%m-%d %H:%M"),
                "symbol": s.symbol,
                "session": s.session_name,
                "setup_type": s.setup_type,
                "direction": s.direction,
                "entry": round(s.entry, 2),
                "stop": round(s.stop, 2),
                "target": round(s.target, 2),
                "dominant_move_direction": s.dominant_move_direction,
                "dominant_move_points": round(s.dominant_move_points, 1),
                "notes": s.classification_notes,
            }
        )

    return pd.DataFrame(rows)
