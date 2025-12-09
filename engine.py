# engine.py
# -------------------------------------
# MT5 connection + auto gold symbol detection
# Order execution engine ONLY
# Strategy logic lives in strategy_engine.py
# -------------------------------------

import MetaTrader5 as mt5
from datetime import datetime
import time


class MT5Engine:
    def __init__(self):
        self.symbol = None

    # ---------------------------------
    # Connect to MT5
    # ---------------------------------
    def connect(self):
        print("\n=== MT5 ENGINE INIT ===")

        if not mt5.initialize():
            raise RuntimeError(f"MT5 INIT FAILED: {mt5.last_error()}")

        account = mt5.account_info()
        if not account:
            raise RuntimeError("❌ Could not access MT5 account")

        print("✅ CONNECTED TO MT5")
        print("Login:", account.login)
        print("Broker:", account.company)
        print("Balance:", account.balance)

        self.symbol = self.detect_gold_symbol()
        print(f"✅ GOLD SYMBOL DETECTED: {self.symbol}")

    # ---------------------------------
    # Auto-detect gold instrument name
    # ---------------------------------
    def detect_gold_symbol(self):
        symbols = mt5.symbols_get()

        gold_candidates = []

        for s in symbols:
            name = s.name.upper()
            if "XAUUSD" in name or "GOLD" in name:
                gold_candidates.append(s.name)

        if not gold_candidates:
            raise RuntimeError("❌ Could not find ANY gold symbols on broker")

        print("\n🪙 Gold symbols found:")
        for sym in gold_candidates:
            print(" -", sym)

        return gold_candidates[0]

    # ---------------------------------
    # Pull recent candles safely
    # ---------------------------------
    def get_candles(self, timeframe=mt5.TIMEFRAME_M15, bars=50):
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, bars)

        if rates is None:
            raise RuntimeError(f"MT5 DATA ERROR: {mt5.last_error()}")

        candles = []

        for r in rates:
            candles.append({
                "time": datetime.fromtimestamp(r['time']),
                "open": round(r['open'], 2),
                "high": round(r['high'], 2),
                "low": round(r['low'], 2),
                "close": round(r['close'], 2)
            })

        return candles

    # ---------------------------------
    # Place market order
    # ---------------------------------
    def place_trade(self, side, lot=0.01, sl_points=300, tp_points=600):

        tick = mt5.symbol_info_tick(self.symbol)

        if tick is None:
            raise RuntimeError("❌ Could not fetch tick data")

        price = tick.ask if side == "buy" else tick.bid
        point = mt5.symbol_info(self.symbol).point

        sl = price - sl_points * point if side == "buy" else price + sl_points * point
        tp = price + tp_points * point if side == "buy" else price - tp_points * point

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 777,
            "comment": "Gold Gladiator AI",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"❌ ORDER FAILED: {result.comment}")

        print("\n✅ ORDER PLACED")
        print("Type:", side)
        print("Entry:", price)
        print("SL:", round(sl, 2))
        print("TP:", round(tp, 2))

        return result

    # ---------------------------------
    # Shutdown MT5
    # ---------------------------------
    def shutdown(self):
        mt5.shutdown()
        print("\n✅ MT5 CONNECTION CLOSED")


# -------------------------------------
# Stand-alone test
# -------------------------------------
if __name__ == "__main__":
    engine = MT5Engine()
    engine.connect()

    candles = engine.get_candles()
    for c in candles[-10:]:
        print(c)

    engine.shutdown()
