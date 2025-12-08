# ============================
# GOLD GLADIATOR ENGINE
# ============================

import MetaTrader5 as mt5
from datetime import datetime, timezone
from dataclasses import dataclass

# ----------------------------------------------------
# Initialize MT5
# ----------------------------------------------------

if not mt5.initialize():
    raise RuntimeError("MT5 failed to initialize")

# ----------------------------------------------------
# Data structure
# ----------------------------------------------------

@dataclass
class TradeSignal:
    symbol: str
    direction: str
    setup_type: int
    session: str
    entry: float
    sl: float
    tp: float
    reason: str
    has_signal: bool


# ----------------------------------------------------
# Sessions
# ----------------------------------------------------

def get_session():
    utc_hour = datetime.now(timezone.utc).hour
    
    if 7 <= utc_hour < 11:
        return "London"
    elif 13 <= utc_hour < 17:
        return "New York"
    else:
        return None


# ----------------------------------------------------
# Candle retrieval
# ----------------------------------------------------

def get_candles(symbol, timeframe, count=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        return None
    return rates


# ----------------------------------------------------
# Structure break check
# ----------------------------------------------------

def break_of_structure(candles):
    highs = [c['high'] for c in candles[-6:-1]]
    lows  = [c['low'] for c in candles[-6:-1]]

    last = candles[-1]

    if last['close'] > max(highs):
        return "BULL"
    if last['close'] < min(lows):
        return "BEAR"

    return None


# ----------------------------------------------------
# Engulfing confirmation
# ----------------------------------------------------

def engulfing(candles):
    prev = candles[-2]
    curr = candles[-1]

    # Bullish engulfing
    if curr['close'] > prev['high']:
        return "BUY"

    # Bearish engulfing
    if curr['close'] < prev['low']:
        return "SELL"

    return None


# ----------------------------------------------------
# MAIN STRATEGY CHECK
# ----------------------------------------------------

def evaluate_setups(symbol="XAUUSD"):

    session = get_session()
    
    # No trading outside session windows
    if session is None:
        return TradeSignal(
            symbol=symbol,
            direction=None,
            setup_type=0,
            session=None,
            entry=0,
            sl=0,
            tp=0,
            reason="Outside London / New York session",
            has_signal=False
        )

    m15 = get_candles(symbol, mt5.TIMEFRAME_M15)
    m5  = get_candles(symbol, mt5.TIMEFRAME_M5)

    if m15 is None or m5 is None:
        return None

    structure = break_of_structure(m15)

    # No structure break = no trade
    if structure is None:
        return TradeSignal(
            symbol=symbol,
            direction=None,
            setup_type=0,
            session=session,
            entry=0,
            sl=0,
            tp=0,
            reason="No break of structure",
            has_signal=False
        )

    confirm = engulfing(m5)

    # No engulfing = no trade
    if confirm is None:
        return TradeSignal(
            symbol=symbol,
            direction=None,
            setup_type=0,
            session=session,
            entry=0,
            sl=0,
            tp=0,
            reason="No engulfing confirmation",
            has_signal=False
        )

    direction = confirm

    entry = m5[-1]['close']

    # Basic SL/TP logic
    sl = entry - 30 if direction == "BUY" else entry + 30
    tp = entry + 90 if direction == "BUY" else entry - 90

    setup = 1 if structure == "BEAR" or structure == "BULL" else 2

    return TradeSignal(
        symbol=symbol,
        direction=direction,
        setup_type=setup,
        session=session,
        entry=round(entry,2),
        sl=round(sl,2),
        tp=round(tp,2),
        reason="Manipulation -> BOS -> Engulfing confirmation",
        has_signal=True
    )


# ----------------------------------------------------
# STREAMLIT INTERFACE CALL
# ----------------------------------------------------

def scan_market(symbol="XAUUSD"):

    result = evaluate_setups(symbol)

    if result is None or not result.has_signal:
        return None

    return {
        "symbol": result.symbol,
        "direction": result.direction,
        "setup_type": result.setup_type,
        "session": result.session,
        "entry": result.entry,
        "sl": result.sl,
        "tp": result.tp,
        "reason": result.reason,
    }
