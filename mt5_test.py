import MetaTrader5 as mt5
from datetime import datetime

# ============================
# AUTO-DETECT GOLD SYMBOL
# ============================

def find_gold_symbol():
    """
    Try to find the broker's gold symbol automatically.
    Looks for anything with 'XAU' in the name first,
    then falls back to names containing 'GOLD'.
    """
    symbols = mt5.symbols_get()
    if symbols is None:
        return None

    # Prefer XAUUSD-style symbols
    xau_candidates = [s.name for s in symbols if "XAU" in s.name.upper()]
    if xau_candidates:
        # If there are several, pick the one that also has USD if possible
        usd_candidates = [s for s in xau_candidates if "USD" in s]
        if usd_candidates:
            return usd_candidates[0]
        return xau_candidates[0]

    # Fallback: anything with GOLD in name
    gold_candidates = [s.name for s in symbols if "GOLD" in s.name.upper()]
    if gold_candidates:
        return gold_candidates[0]

    return None


def main():
    print("\n===== GOLD GLADIATOR MT5 TEST =====")

    # ----------------------------
    # INIT
    # ----------------------------
    if not mt5.initialize():
        print("❌ MT5 failed to initialize")
        print("MT5 init error:", mt5.last_error())
        return

    print("✅ MT5 initialized successfully")

    account_info = mt5.account_info()
    if account_info is None:
        print("❌ Failed to read account info")
        print("MT5 error:", mt5.last_error())
        mt5.shutdown()
        return

    print("\n✅ CONNECTED TO MT5")
    print("---------------------------")
    print(f"Login:   {account_info.login}")
    print(f"Name:    {account_info.name}")
    print(f"Server:  {account_info.server}")
    print(f"Balance: {account_info.balance}")
    print(f"Equity:  {account_info.equity}")
    print("---------------------------")

    # ----------------------------
    # FIND GOLD SYMBOL
    # ----------------------------
    gold_symbol = find_gold_symbol()

    if gold_symbol is None:
        print("\n❌ Could not find any gold symbol (XAU or GOLD) on this MT5.")
        print("Tip: open MT5 → Market Watch → Show All, then run this again.")
        mt5.shutdown()
        return

    print(f"\n✅ Detected gold symbol: {gold_symbol}")

    # Make sure it's visible in Market Watch
    symbol_info = mt5.symbol_info(gold_symbol)
    if symbol_info is None:
        print(f"\n❌ Symbol '{gold_symbol}' disappeared or is invalid.")
        mt5.shutdown()
        return

    if not symbol_info.visible:
        print(f"ℹ️ Symbol '{gold_symbol}' is hidden. Trying to enable it...")
        if not mt5.symbol_select(gold_symbol, True):
            print(f"❌ Failed to enable symbol '{gold_symbol}' in Market Watch.")
            print("MT5 error:", mt5.last_error())
            mt5.shutdown()
            return

    print(f"✅ Symbol '{gold_symbol}' is available and visible.")

    # ----------------------------
    # FETCH CANDLES (M15)
    # ----------------------------
    TIMEFRAME = mt5.TIMEFRAME_M15
    CANDLES_TO_FETCH = 20

    print(f"\nFetching last {CANDLES_TO_FETCH} M15 candles on {gold_symbol}...")

    rates = mt5.copy_rates_from_pos(gold_symbol, TIMEFRAME, 0, CANDLES_TO_FETCH)

    if rates is None:
        print("\n❌ FAILED TO GET CANDLE DATA")
        print("MT5 error:", mt5.last_error())
    else:
        print(f"\n✅ LAST {CANDLES_TO_FETCH} M15 CANDLES ({gold_symbol})")
        for r in rates:
            t = datetime.fromtimestamp(r['time'])
            print({
                "time": t.strftime("%Y-%m-%d %H:%M"),
                "open": round(r['open'], 2),
                "high": round(r['high'], 2),
                "low": round(r['low'], 2),
                "close": round(r['close'], 2),
            })

    # ----------------------------
    # SHUTDOWN
    # ----------------------------
    mt5.shutdown()
    print("\n✅ MT5 CONNECTION TEST COMPLETE")


if __name__ == "__main__":
    main()
