import MetaTrader5 as mt5
from datetime import datetime, timedelta

SYMBOL = "XAUUSD"      # change if your broker uses a different name
TIMEFRAME = mt5.TIMEFRAME_M15
CANDLES = 20

print("=== MT5 CONNECTION TEST ===")

# 1) Initialize connection
if not mt5.initialize():
    print("❌ initialize() failed")
    print("error code:", mt5.last_error())
    quit()

# 2) Show account info (must have MT5 terminal open & logged in)
account_info = mt5.account_info()
if account_info is None:
    print("❌ No account info. Is MT5 terminal open and logged in?")
    mt5.shutdown()
    quit()

print(f"✅ Connected to account: {account_info.login}")
print(f"   Balance: {account_info.balance}, Equity: {account_info.equity}")

# 3) Get last N candles
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, CANDLES)
if rates is None:
    print("❌ Could not read candles. Check symbol name:", SYMBOL)
    mt5.shutdown()
    quit()

print(f"\n✅ Got last {len(rates)} candles for {SYMBOL} on M15:")
for r in rates:
    t = datetime.fromtimestamp(r['time'])
    print(
        t,
        "O:", r['open'],
        "H:", r['high'],
        "L:", r['low'],
        "C:", r['close']
    )

mt5.shutdown()
print("\n✅ MT5 test finished OK.")
