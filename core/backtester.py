"""
Vectorized triple-barrier backtester.
Educational / research use only.
"""

import numpy as np
import pandas as pd
from core.labeling import get_daily_vol


def vectorized_triple_barrier_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    pt_sl: list = [1.8, 1.2],
    vertical_bars: int = 12,
    commission: float = 0.0002,
    slippage: float = 0.00015,
):
    """
    Fast vectorized backtest that respects profit-take, stop-loss
    and vertical (time) barriers + realistic transaction costs.
    """
    close = df["Close"]
    vol = get_daily_vol(close)
    equity = pd.Series(1.0, index=df.index)
    trades = []

    i = 0
    n = len(df)
    while i < n - vertical_bars - 1:
        if signals.iloc[i] == 0:
            i += 1
            continue

        side = float(signals.iloc[i])
        entry = float(close.iloc[i])
        trgt = float(vol.iloc[i]) if not np.isnan(vol.iloc[i]) else 0.001

        pt = entry * (1 + side * pt_sl[0] * trgt)
        sl = entry * (1 - side * pt_sl[1] * trgt)
        t1_idx = min(i + vertical_bars, n - 1)

        path = close.iloc[i + 1 : t1_idx + 1]
        exit_price = float(path.iloc[-1])
        exit_idx = path.index[-1]
        reason = "vertical"

        if side == 1:
            hit_pt = path[path >= pt]
            hit_sl = path[path <= sl]
        else:
            hit_pt = path[path <= pt]
            hit_sl = path[path >= sl]

        if len(hit_pt) > 0:
            exit_price = float(hit_pt.iloc[0])
            exit_idx = hit_pt.index[0]
            reason = "pt"
        if len(hit_sl) > 0 and (len(hit_pt) == 0 or hit_sl.index[0] < hit_pt.index[0]):
            exit_price = float(hit_sl.iloc[0])
            exit_idx = hit_sl.index[0]
            reason = "sl"

        cost = (commission + slippage) * 2
        ret = side * (exit_price / entry - 1) - cost
        equity.loc[exit_idx:] *= 1 + ret

        trades.append(
            {
                "entry_time": str(df.index[i]),
                "exit_time": str(exit_idx),
                "side": int(side),
                "entry": entry,
                "exit": exit_price,
                "ret": float(ret),
                "reason": reason,
            }
        )
        i = df.index.get_loc(exit_idx) + 1

    trade_df = pd.DataFrame(trades)
    if len(trade_df) == 0:
        stats = {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_ret": 0.0,
            "sharpe": 0.0,
            "max_dd": 0.0,
            "final_equity": 1.0,
        }
    else:
        stats = {
            "total_trades": int(len(trade_df)),
            "win_rate": float((trade_df["ret"] > 0).mean()),
            "avg_ret": float(trade_df["ret"].mean()),
            "sharpe": float(
                trade_df["ret"].mean() / (trade_df["ret"].std() + 1e-9) * np.sqrt(252 * 24)
            ),
            "max_dd": float((equity / equity.cummax() - 1).min()),
            "final_equity": float(equity.iloc[-1]),
        }
    return equity, trade_df, stats
