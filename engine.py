import datetime as dt
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import numpy as np

try:
    import MetaTrader5 as mt5  # type: ignore
except Exception:  # MetaTrader5 might not exist in some environments
    mt5 = None  # type: ignore


@dataclass
class TradeSignal:
    time: dt.datetime
    symbol: str
    timeframe: str
    direction: str  # 'buy' or 'sell'
    setup: str      # 'setup1' or 'setup2' or 'momentum'
    entry: float
    stop_loss: float
    take_profit: float
    risk_r: float


class StrategyEngine:
    """
    First wiring of your Gold setup scanner.

    This version is intentionally simple & safe:
    - It only scans one symbol (your GOLD symbol on the current MT5 account)
    - It looks for a strong intraday impulse move and proposes 1 momentum trade
      in the direction of that move.
    - It NEVER sends orders. It only returns TradeSignal objects for the UI.
    """

    def __init__(self, risk_per_trade_pct: float = 1.0) -> None:
        self.risk_per_trade_pct = risk_per_trade_pct

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _require_mt5(self) -> None:
        if mt5 is None:
            raise RuntimeError("MetaTrader5 package is not available in this Python environment.")

    def find_gold_symbol(self) -> Optional[str]:
        """
        Try to locate the GOLD symbol on the connected MT5 server.

        1) Check a list of common names.
        2) If nothing matches, fall back to the first symbol that contains 'XAU'.
        """
        self._require_mt5()

        candidates = [
            "XAUUSD",
            "XAUUSD.",
            "XAUUSDm",
            "XAUUSDmicro",
            "GOLD",
            "GOLDmicro",
            "XAUUSD-Var",
            "XAUUSD.pro",
            "XAUUSD.cash",
        ]

        symbols = mt5.symbols_get()
        if symbols is None:
            return None

        upper_to_name = {s.name.upper(): s.name for s in symbols}

        # 1) Exact candidates
        for c in candidates:
            if c.upper() in upper_to_name:
                return upper_to_name[c.upper()]

        # 2) Anything containing "XAU"
        for s in symbols:
            if "XAU" in s.name.upper():
                return s.name

        return None

    def _load_candles(
        self,
        symbol: str,
        timeframe: Any,
        count: int = 300,
    ) -> Optional[np.ndarray]:
        """Load recent candles from MT5."""
        self._require_mt5()

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            return None
        return rates

    # ------------------------------------------------------------------
    # Public API used by the Streamlit app
    # ------------------------------------------------------------------
    def get_account_snapshot(self) -> Optional[Dict[str, float]]:
        """
        Fetch live account info from the currently-connected MT5 terminal.

        Returns None if MT5 is not connected.
        """
        self._require_mt5()

        info = mt5.account_info()
        if info is None:
            return None

        return {
            "login": float(info.login),
            "balance": float(info.balance),
            "equity": float(info.equity),
            "margin": float(info.margin),
            "margin_free": float(info.margin_free),
        }

    def scan_gold_momentum(self) -> List[TradeSignal]:
        """
        Very first 'in action' scan.

        Logic (kept simple on purpose so it’s robust):
        - Find GOLD symbol on this MT5.
        - Pull ~200 candles on M15.
        - Measure the move from 20 bars ago to now.
        - If move is strong enough, propose ONE momentum trade in that direction,
          with a stop behind the recent swing and TP at 2R.
        """

        self._require_mt5()

        symbol = self.find_gold_symbol()
        if symbol is None:
            return []

        candles = self._load_candles(symbol, mt5.TIMEFRAME_M15, count=200)
        if candles is None or len(candles) < 30:
            return []

        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c["high"] for c in candles], dtype=float)
        lows = np.array([c["low"] for c in candles], dtype=float)
        times = np.array([dt.datetime.fromtimestamp(c["time"]) for c in candles])

        last_close = closes[-1]
        lookback = 20
        ref_close = closes[-lookback]

        move_points = last_close - ref_close
        move_pct = move_points / ref_close * 100.0

        # Require at least 0.3% move to consider it a "clear" intraday impulse.
        min_move_pct = 0.3

        if abs(move_pct) < min_move_pct:
            # No strong move -> no trade.
            return []

        if move_points > 0:
            direction = "buy"
            setup = "momentum_up"
            # stop below recent swing low
            recent_low = float(lows[-10:].min())
            entry = float(last_close)
            stop_loss = recent_low
        else:
            direction = "sell"
            setup = "momentum_down"
            # stop above recent swing high
            recent_high = float(highs[-10:].max())
            entry = float(last_close)
            stop_loss = recent_high

        # Basic 2R take-profit around that stop distance
        if direction == "buy":
            risk_per_unit = entry - stop_loss
            if risk_per_unit <= 0:
                return []
            take_profit = entry + 2.0 * risk_per_unit
        else:
            risk_per_unit = stop_loss - entry
            if risk_per_unit <= 0:
                return []
            take_profit = entry - 2.0 * risk_per_unit

        risk_r = 2.0  # by construction

        signal = TradeSignal(
            time=times[-1],
            symbol=symbol,
            timeframe="M15",
            direction=direction,
            setup=setup,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_r=risk_r,
        )

        return [signal]
