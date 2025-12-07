import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import time

SYMBOL = "GOLD"

TF_M15 = mt5.TIMEFRAME_M15
TF_M5 = mt5.TIMEFRAME_M5


# ------------------------------
# INITIALIZE MT5
# ------------------------------

if not mt5.initialize():
    print("❌ MT5 INITIALIZATION FAILED:", mt5.last_error())
    quit()

print("✅ MT5 CONNECTED")

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------

def fetch_candles(tf, count=20):
    rates = mt5.copy_rates_from_pos(SYMBOL, tf, 0, count)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


def is_bullish_engulf(prev, curr):
    return (
        curr['close'] > curr['open']
        and prev['close'] < prev['open']
        and curr['close'] > prev['open']
        and curr['open'] < prev['close']
    )


def is_bearish_engulf(prev, curr):
    return (
        curr['close'] < curr['open']
        and prev['close'] > prev['open']
        and curr['close'] < prev['open']
        and curr['open'] > prev['close']
    )


# ------------------------------
# MAIN LOOP
# ------------------------------

print("\n🚀 STRATEGY ENGINE RUNNING (LIVE MODE)\n")

while True:

    try:
        # ------------------------------
        # GET TIMEFRAMES
        # ------------------------------

        m15 = fetch_candles(TF_M15)
        m5 = fetch_candles(TF_M5)

        prev15 = m15.iloc[-2]
        curr15 = m15.iloc[-1]

        prev5 = m5.iloc[-2]
        curr5 = m5.iloc[-1]

        signal = None

        # ------------------------------
        # M15 CONFIRMATION
        # ------------------------------

        if is_bullish_engulf(prev15, curr15):
            m15_bias = "BUY"
        elif is_bearish_engulf(prev15, curr15):
            m15_bias = "SELL"
        else:
            m15_bias = None

        # ------------------------------
        # M5 EXECUTION
        # ------------------------------

        if m15_bias == "BUY" and is_bullish_engulf(prev5, curr5):
            signal = "BUY"

        elif m15_bias == "SELL" and is_bearish_engulf(prev5, curr5):
            signal = "SELL"


        # ------------------------------
        # OUTPUT SIGNAL
        # ------------------------------

        now = datetime.now().strftime("%H:%M:%S")

        if signal:
            print(f"\n🟢 TRADE SIGNAL [{now}]")
            print("PAIR:", SYMBOL)
            print("DIRECTION:", signal)
            print("M15 ENGULF CONFIRMED")
            print("M5 ENTRY ENGULF CONFIRMED")
            print("PRICE:", curr5['close'])

        else:
            print(f"[{now}] NO SIGNAL – monitoring...")

        time.sleep(5)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(5)


# ------------------------------
# SHUTDOWN
# ------------------------------

mt5.shutdown()
