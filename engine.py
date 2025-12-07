# engine.py
# Core strategy engine for GOLD GLADIATOR
# Uses: time windows + structure break + FVG + engulfing confirmation

import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Tuple

# ----------------------------
# CONFIG
# ----------------------------

# Time windows (NY time, 24h)
SESSION_WINDOWS = [
    ("ASIA",   0,  0,  1,  0),   # 00:00–01:00
    ("LONDON", 3,  0,  5,  0),   # 03:00–05:00
    ("NY",     8,  0, 10,  0),   # 08:00–10:00
]

MAX_RISK_PCT = 10.0        # upper limit for UI; actual % is chosen by user
TP_R_MULT   = 4.0          # default R-multiple target

# swing detection settings
SWING_LOOKBACK = 2         # bars left/right to consider local swing

# ----------------------------
# DATASTRUCTURES
# ----------------------------

@dataclass
class Trade:
    time: pd.Timestamp
    direction: str         # 'BUY' or 'SELL'
    entry: float
    sl: float
    tp: float
    session: str
    tag: str               # e.g. "Core Setup v1"
    status: str            # 'OPEN', 'TP', 'SL'

# ----------------------------
# UTIL FUNCTIONS
# ----------------------------

def mark_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns: hour, minute, session_name, in_window."""
    df = df.copy()
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute

    session_name = []
    in_window = []
    for h, m in zip(df["hour"], df["minute"]):
        s_name = None
        inside = False
        for name, sh, sm, eh, em in SESSION_WINDOWS:
            after_start = (h > sh) or (h == sh and m >= sm)
            before_end  = (h < eh) or (h == eh and m < em)
            if after_start and before_end:
                s_name = name
                inside = True
                break
        session_name.append(s_name)
        in_window.append(inside)

    df["session"] = session_name
    df["in_window"] = in_window
    return df


def find_swings(df: pd.DataFrame) -> pd.DataFrame:
    """Simple fractal-based swings."""
    df = df.copy()
    highs = df["high"].values
    lows = df["low"].values

    swing_high = [False] * len(df)
    swing_low  = [False] * len(df)

    for i in range(SWING_LOOKBACK, len(df) - SWING_LOOKBACK):
        left_highs  = highs[i-SWING_LOOKBACK:i]
        right_highs = highs[i+1:i+1+SWING_LOOKBACK]
        if highs[i] > max(left_highs) and highs[i] > max(right_highs):
            swing_high[i] = True

        left_lows  = lows[i-SWING_LOOKBACK:i]
        right_lows = lows[i+1:i+1+SWING_LOOKBACK]
        if lows[i] < min(left_lows) and lows[i] < min(right_lows):
            swing_low[i] = True

    df["swing_high"] = swing_high
    df["swing_low"] = swing_low
    return df


def detect_fvg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Very simple 3-candle FVG:
    Bullish FVG: low[i] > high[i-2]
    Bearish FVG: high[i] < low[i-2]
    """
    df = df.copy()
    bullish_fvg = [False] * len(df)
    bearish_fvg = [False] * len(df)

    for i in range(2, len(df)):
        if df["low"].iloc[i] > df["high"].iloc[i-2]:
            bullish_fvg[i] = True
        if df["high"].iloc[i] < df["low"].iloc[i-2]:
            bearish_fvg[i] = True

    df["bullish_fvg"] = bullish_fvg
    df["bearish_fvg"] = bearish_fvg
    return df


def is_engulfing(prev_open: float, prev_close: float,
                 open_: float, close_: float) -> str:
    """
    Returns 'bull', 'bear' or '' depending on engulfing type.
    Bullish: body up, closes above prev high body.
    Bearish: body down, closes below prev low body.
    """
    # previous body
    prev_body_low = min(prev_open, prev_close)
    prev_body_high = max(prev_open, prev_close)

    # current body
    body_low = min(open_, close_)
    body_high = max(open_, close_)

    if close_ > open_:  # bullish body
        if body_low <= prev_body_low and body_high >= prev_body_high:
            return "bull"
    elif close_ < open_:  # bearish body
        if body_high >= prev_body_high and body_low <= prev_body_low:
            return "bear"
    return ""


# ----------------------------
# CORE ENGINE
# ----------------------------

def scan_setups(df_raw: pd.DataFrame,
                risk_pct: float = 1.0,
                tp_R: float = TP_R_MULT) -> Tuple[List[Trade], Dict[str, float]]:
    """
    Main engine:
    - df_raw: M5 OHLCV data with datetime index
    - risk_pct: user-selected % risk per trade (0–10)
    """
    # clamp risk
    risk_pct = max(0.1, min(risk_pct, MAX_RISK_PCT))

    df = df_raw.copy()
    df = mark_sessions(df)
    df = find_swings(df)
    df = detect_fvg(df)

    trades: List[Trade] = []
    open_trades_idx: List[int] = []

    # Track swings (simple BOS idea)
    last_swing_high_price = None
    last_swing_low_price = None
    trend_direction = None  # 'UP' or 'DOWN'

    for i in range(2, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # Update swing memory
        if row["swing_high"]:
            last_swing_high_price = row["high"]
        if row["swing_low"]:
            last_swing_low_price = row["low"]

        # Determine simple trend direction (BOS)
        if last_swing_high_price is not None and row["close"] > last_swing_high_price:
            trend_direction = "UP"
        if last_swing_low_price is not None and row["close"] < last_swing_low_price:
            trend_direction = "DOWN"

        # Manage open trades (TP / SL check)
        if open_trades_idx:
            # iterate over a copy of indices, remove as they close
            for idx in open_trades_idx[:]:
                t = trades[idx]
                high_i = row["high"]
                low_i = row["low"]

                if t.status == "OPEN":
                    if t.direction == "BUY":
                        if low_i <= t.sl:
                            t.status = "SL"
                            open_trades_idx.remove(idx)
                        elif high_i >= t.tp:
                            t.status = "TP"
                            open_trades_idx.remove(idx)
                    else:  # SELL
                        if high_i >= t.sl:
                            t.status = "SL"
                            open_trades_idx.remove(idx)
                        elif low_i <= t.tp:
                            t.status = "TP"
                            open_trades_idx.remove(idx)

        # Only look for new setups in time window
        if not row["in_window"]:
            continue

        # Confirmation candle engulfing
        eng_type = is_engulfing(prev["open"], prev["close"],
                                row["open"], row["close"])
        if eng_type == "":
            continue

        # Direction filter from simple trend
        if eng_type == "bull" and trend_direction != "UP":
            continue
        if eng_type == "bear" and trend_direction != "DOWN":
            continue

        # FVG in the direction of trade near price
        if eng_type == "bull":
            if not any(df["bullish_fvg"].iloc[max(0, i-3):i+1]):
                continue
        if eng_type == "bear":
            if not any(df["bearish_fvg"].iloc[max(0, i-3):i+1]):
                continue

        # Build trade object
        time_i = row.name
        direction = "BUY" if eng_type == "bull" else "SELL"

        entry = row["close"]

        # SL = second swing behind entry (approx: last opposite swing)
        if direction == "BUY" and last_swing_low_price is not None:
            sl = float(last_swing_low_price)
        elif direction == "SELL" and last_swing_high_price is not None:
            sl = float(last_swing_high_price)
        else:
            continue  # if no swing, skip

        # Protect against zero or inverted SL
        if direction == "BUY" and sl >= entry:
            continue
        if direction == "SELL" and sl <= entry:
            continue

        risk_per_unit = abs(entry - sl)
        if risk_per_unit <= 0:
            continue

        # TP by R-multiple
        if direction == "BUY":
            tp = entry + tp_R * risk_per_unit
        else:
            tp = entry - tp_R * risk_per_unit

        new_trade = Trade(
            time=time_i,
            direction=direction,
            entry=float(entry),
            sl=float(sl),
            tp=float(tp),
            session=row["session"] or "",
            tag="Core Setup v1",
            status="OPEN"
        )
        trades.append(new_trade)
        open_trades_idx.append(len(trades) - 1)

    # Compute stats
    total = len(trades)
    closed = [t for t in trades if t.status in ("TP", "SL")]
    wins = [t for t in closed if t.status == "TP"]
    losses = [t for t in closed if t.status == "SL"]

    stats = {
        "setups_found": total,
        "completed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "winrate_pct": (len(wins) / len(closed) * 100.0) if closed else 0.0,
    }

    return trades, stats


# Helper: convert trades list to DataFrame for UI
def trades_to_df(trades: List[Trade]) -> pd.DataFrame:
    rows = []
    for t in trades:
        rows.append({
            "Time": t.time,
            "Direction": t.direction,
            "Entry": t.entry,
            "SL": t.sl,
            "TP": t.tp,
            "Session": t.session,
            "Tag": t.tag,
            "Status": t.status,
        })
    return pd.DataFrame(rows).set_index("Time").sort_index()
