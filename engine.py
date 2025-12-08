"""
Joshua Strategy Engine

STRICTLY follows Joshua's trading rules:

WORKFLOW PER SESSION:
1. Start FROM SESSION WINDOW.
2. Look LEFT to the start of the day.
3. Determine:
      - SETUP 1 = Manipulation then BOS
      - SETUP 2 = Impulse BOS then retrace (no manipulation)
4. Wait for retrace into FVG + OB.
5. Confirm with ENGULFING candle *inside session window*.
6. Entry = engulf close.
"""

import pandas as pd
from typing import List
from dataclasses import dataclass

# -----------------------------------------------------
# Time Windows (NEW YORK)
# -----------------------------------------------------
SESSIONS = [
    ("LONDON", 3, 5),
    ("NEW_YORK", 8, 10)
]

# -----------------------------------------------------
@dataclass
class TradeSignal:
    symbol: str
    session: str
    setup: str
    direction: str
    entry: float
    stop: float
    target: float
    time: pd.Timestamp


# -----------------------------------------------------

def engulfing(prev, curr, direction):
    if direction == "BUY":
        return (
            curr["close"] > curr["open"] and
            curr["close"] > prev["high"]
        )

    if direction == "SELL":
        return (
            curr["close"] < curr["open"] and
            curr["close"] < prev["low"]
        )

    return False


# -----------------------------------------------------

def detect_fvg(df, idx, direction):

    if idx < 2:
        return False

    if direction == "BUY":
        return df.iloc[idx - 2]["high"] < df.iloc[idx]["low"]

    if direction == "SELL":
        return df.iloc[idx - 2]["low"] > df.iloc[idx]["high"]

    return False


# -----------------------------------------------------

def detect_setup_type(day_df):

    highs = day_df["high"]
    lows  = day_df["low"]

    high_idx = highs.idxmax()
    low_idx  = lows.idxmin()

    # If low came AFTER big upside = manipulation + BOS → SETUP 1 BUY
    if low_idx > high_idx:
        return "SETUP_1", "BUY"

    # If high came AFTER big downside = manipulation + BOS → SETUP 1 SELL
    if high_idx > low_idx:
        return "SETUP_1", "SELL"

    # Otherwise default = continuation → SETUP 2
    first = day_df.iloc[0]
    last  = day_df.iloc[-1]

    if last["close"] > first["open"]:
        return "SETUP_2", "BUY"

    else:
        return "SETUP_2", "SELL"


# -----------------------------------------------------

def generate_signals(df, symbol="XAUUSD", rr=3.0) -> List[TradeSignal]:

    signals = []

    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    for day, day_df in df.groupby(df.index.date):

        for session_name, start, end in SESSIONS:

            session_df = day_df.between_time(
                f"{start}:00",
                f"{end}:00",
                inclusive="left"
            )

            if session_df.empty:
                continue

            # LOOK LEFT FROM WINDOW -> DAY START
            start_time = session_df.index[0]
            pre_session = day_df[day_df.index < start_time]

            if len(pre_session) < 10:
                continue

            # CLASSIFY STRUCTURE
            setup, direction = detect_setup_type(pre_session)

            # SCAN SESSION FOR FVG + ENGULF
            for i in range(3, len(session_df)):

                if not detect_fvg(session_df, i, direction):
                    continue

                prev = session_df.iloc[i - 1]
                curr  = session_df.iloc[i]

                if engulfing(prev, curr, direction):

                    entry = curr["close"]

                    if direction == "BUY":
                        stop = session_df.iloc[i - 2:i]["low"].min()
                        target = entry + (entry - stop) * rr

                    else:
                        stop = session_df.iloc[i - 2:i]["high"].max()
                        target = entry - (stop - entry) * rr

                    signals.append(
                        TradeSignal(
                            symbol=symbol,
                            session=session_name,
                            setup=setup,
                            direction=direction,
                            entry=round(entry, 2),
                            stop=round(stop, 2),
                            target=round(target, 2),
                            time=curr.name
                        )
                    )

                    break

    return signals
