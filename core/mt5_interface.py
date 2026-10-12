"""
MetaTrader 5 integration skeleton.
ONLY use on a DEMO account after extensive paper testing.
Educational / research use only.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class MT5Interface:
    def __init__(
        self,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        path: Optional[str] = None,
    ):
        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 package is not installed")

        if not mt5.initialize(path=path):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

        if login and password and server:
            authorized = mt5.login(login, password=password, server=server)
            if not authorized:
                raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")

        print("MT5 connected:", mt5.terminal_info())
        print("Account:", mt5.account_info())

    def shutdown(self):
        if MT5_AVAILABLE:
            mt5.shutdown()

    def get_rates(self, symbol: str = "XAUUSD", timeframe=None, n_bars: int = 5000) -> pd.DataFrame:
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
        if rates is None:
            raise RuntimeError(f"Failed to get rates: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df = df[["open", "high", "low", "close", "tick_volume"]].rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "tick_volume": "Volume",
            }
        )
        return df

    def get_current_price(self, symbol: str = "XAUUSD") -> Optional[Dict[str, Any]]:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "time": datetime.fromtimestamp(tick.time),
        }

    def place_order(
        self,
        symbol: str = "XAUUSD",
        order_type: str = "buy",
        volume: float = 0.01,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        comment: str = "ML_Signal",
    ):
        """Market order – DEMO only."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise RuntimeError(f"{symbol} not found")
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if order_type == "buy" else tick.bid
        order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type_mt5,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 20261012,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.retcode} – {result.comment}")
            return None
        print(f"Order placed: {order_type} {volume} lots @ {price}")
        return result

    def get_open_positions(self, symbol: str = "XAUUSD"):
        positions = mt5.positions_get(symbol=symbol)
        return list(positions) if positions else []
