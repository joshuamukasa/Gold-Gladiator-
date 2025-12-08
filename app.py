import streamlit as st
import datetime as dt
from datetime import timedelta
import numpy as np
import MetaTrader5 as mt5

# --------------------------------------------------
# BASIC PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Gold Gladiator",
    layout="wide",
)

st.title("GOLD GLADIATOR")
st.caption("Intraday AI execution surface for your New York & London trading framework.")

# --------------------------------------------------
# HELPER: CONNECT TO MT5
# --------------------------------------------------
def connect_mt5():
    if not mt5.initialize():
        return False, mt5.last_error()
    return True, None

def shutdown_mt5():
    mt5.shutdown()

# --------------------------------------------------
# HELPER: GET TODAY'S CANDLES (M5 / M15)
# --------------------------------------------------
TIMEFRAME_MAP = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
}

def get_today_candles(symbol: str, tf_label: str):
    tf = TIMEFRAME_MAP[tf_label]

    now = dt.datetime.now()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # we’ll pull enough candles to safely cover today
    rates = mt5.copy_rates_range(
        symbol,
        tf,
        today_midnight,
        now,
    )

    if rates is None or len(rates) == 0:
        return None

    return rates

# --------------------------------------------------
# VERY SIMPLE STRUCTURE ANALYSIS
# (This is a first pass, not perfect ICT logic.)
# --------------------------------------------------
def detect_setup_direction(rates: np.ndarray):
    """
    Very simple, rule-of-thumb intraday bias detector.

    - If price clearly trends UP today  -> bias = BUY
    - If price clearly trends DOWN      -> bias = SELL
    - Otherwise                         -> NO-TRADE

    This is only a shell so we can see signals on the dashboard.
    We will refine with your full Setup 1 / Setup 2 logic.
    """
    closes = np.array([r["close"] for r in rates], dtype=float)

    if len(closes) < 10:
        return "NO-TRADE", "Not enough candles for today."

    day_low = closes.min()
    day_high = closes.max()
    open_price = closes[0]
    last_price = closes[-1]

    range_points = day_high - day_low
    if range_points <= 0:
        return "NO-TRADE", "Flat day, no range."

    # how far did we move away from the day's low & high?
    dist_from_low = last_price - day_low
    dist_from_high = day_high - last_price

    # simple directional thresholds (can be tightened later)
    up_strength = dist_from_low / range_points
    down_strength = dist_from_high / range_points

    # If we’re near the top of the range and well above the low -> buyers in control
    if up_strength > 0.65 and last_price > open_price:
        return "BUY", f"Strong move up within today's range (score {up_strength:.2f})."

    # If we’re near the bottom of the range and well below the high -> sellers in control
    if down_strength > 0.65 and last_price < open_price:
        return "SELL", f"Strong move down within today's range (score {down_strength:.2f})."

    return "NO-TRADE", "No clear directional dominance today."

# --------------------------------------------------
# RISK & TRADE SIZING
# --------------------------------------------------
def estimate_trade_size(balance: float, risk_pct: float, stop_distance_points: float, value_per_point: float):
    """
    Very simple risk model: risk_pct of balance / (stop x value_per_point).
    For now we’ll assume a rough value_per_point for gold & euro.
    """
    if balance <= 0 or stop_distance_points <= 0 or value_per_point <= 0:
        return 0.0

    risk_money = balance * (risk_pct / 100.0)
    lots = risk_money / (stop_distance_points * value_per_point)
    return round(lots, 2)

def guess_tick_value(symbol: str) -> float:
    """
    Rough value per point, used *only* for a first pass risk preview.
    You can refine later with your broker’s exact tick sizes.
    """
    symbol = symbol.upper()
    if "XAU" in symbol:
        return 1.0  # placeholder: 1$ per point
    if "EURUSD" in symbol or "GBPUSD" in symbol:
        return 0.1  # placeholder
    return 0.1

# --------------------------------------------------
# SIDEBAR CONTROLS
# --------------------------------------------------
st.sidebar.subheader("Execution parameters")

risk_pct = st.sidebar.slider(
    "Risk per trade (%)",
    min_value=0.25,
    max_value=10.0,
    value=1.0,
    step=0.25,
)

symbol = st.sidebar.selectbox(
    "Symbol",
    options=["XAUUSD", "EURUSD"],
    index=0,
)

tf_label = st.sidebar.radio(
    "Trading timeframe",
    options=["M5", "M15"],
    index=1,
)

st.sidebar.markdown("---")
st.sidebar.caption("This shell app runs your intraday framework.\n"
                   "Next step is wiring in your full Setup 1 / Setup 2 logic.")

# --------------------------------------------------
# MAIN LAYOUT – METRICS
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("ACCOUNT BALANCE", "—")
with col2:
    st.metric("NET P/L (SESSION)", "—")
with col3:
    st.metric("WIN RATE", "—")
with col4:
    st.metric("RISK PER TRADE", f"{risk_pct:.2f}%")

st.markdown("### Equity / Performance")
equity_placeholder = st.empty()
equity_placeholder.line_chart([0])  # placeholder flat line

st.markdown("---")

# --------------------------------------------------
# ACTION BUTTON – SCAN MARKET
# --------------------------------------------------
st.markdown("### Intraday scan")

st.write(
    "Click the button below to let the system read **today's candles** "
    f"for **{symbol} ({tf_label})**, apply the basic intraday rules, "
    "and return either **BUY**, **SELL**, or **NO-TRADE**."
)

scan_button = st.button("🔍 Scan today for setups")

result_box = st.empty()

if scan_button:
    with st.spinner("Connecting to MT5 and reading today's candles..."):
        ok, err = connect_mt5()
        if not ok:
            result_box.error(f"MT5 connection failed: {err}")
        else:
            rates = get_today_candles(symbol, tf_label)
            if rates is None:
                result_box.error("Could not load today's candles for this symbol / timeframe.")
            else:
                direction, explanation = detect_setup_direction(rates)

                if direction == "NO-TRADE":
                    result_box.warning(f"NO-TRADE: {explanation}")
                elif direction == "BUY":
                    # simple placeholder position sizing
                    balance_preview = 10000.0  # until we pull live balance from MT5
                    stop_points = 34.0         # your default stop distance
                    value_per_point = guess_tick_value(symbol)
                    lots = estimate_trade_size(
                        balance_preview,
                        risk_pct,
                        stop_points,
                        value_per_point,
                    )
                    result_box.success(
                        f"✅ BUY setup detected.\n\n"
                        f"- Direction: **LONG {symbol}**\n"
                        f"- Reason: {explanation}\n"
                        f"- Risk: **{risk_pct:.2f}%** of balance\n"
                        f"- Approx. lot size (demo balance {balance_preview:.0f}): **{lots} lots**\n"
                        f"- Assumed stop: **{stop_points} points**"
                    )
                elif direction == "SELL":
                    balance_preview = 10000.0
                    stop_points = 34.0
                    value_per_point = guess_tick_value(symbol)
                    lots = estimate_trade_size(
                        balance_preview,
                        risk_pct,
                        stop_points,
                        value_per_point,
                    )
                    result_box.success(
                        f"✅ SELL setup detected.\n\n"
                        f"- Direction: **SHORT {symbol}**\n"
                        f"- Reason: {explanation}\n"
                        f"- Risk: **{risk_pct:.2f}%** of balance\n"
                        f"- Approx. lot size (demo balance {balance_preview:.0f}): **{lots} lots**\n"
                        f"- Assumed stop: **{stop_points} points**"
                    )

            shutdown_mt5()
