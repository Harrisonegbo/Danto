"""
Advanced Gymnasium environment for XAUUSD with sophisticated reward shaping.
Educational / research use only.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np


class AdvancedXAUUSDEnv(gym.Env):
    """
    Custom trading environment.
    Action space: Discrete(3) → 0=flat, 1=long, 2=short
    Observation: window of features + position + unrealized PnL + drawdown
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df,
        feature_cols,
        window: int = 32,
        initial_balance: float = 10000.0,
        commission: float = 0.0002,
        slippage: float = 0.00015,
        max_dd_limit: float = 0.08,
    ):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.window = window
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        self.max_dd_limit = max_dd_limit

        self.action_space = spaces.Discrete(3)
        n_feat = len(feature_cols) + 3  # + pos, upnl, drawdown
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(window, n_feat), dtype=np.float32
        )
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_idx = self.window
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.peak_equity = self.initial_balance
        self.position = 0.0
        self.entry_price = 0.0
        self.equity_curve = [self.equity]
        self.returns = []
        return self._get_obs(), {}

    def _get_obs(self):
        start = self.step_idx - self.window
        feats = self.df.loc[start : self.step_idx - 1, self.feature_cols].values.astype(np.float32)
        pos = np.full((self.window, 1), self.position, dtype=np.float32)

        upnl = 0.0
        if self.position != 0:
            price = float(self.df.loc[self.step_idx - 1, "Close"])
            upnl = (price / self.entry_price - 1) * self.position
        upnl_arr = np.full((self.window, 1), upnl, dtype=np.float32)

        dd = self.equity / self.peak_equity - 1
        dd_arr = np.full((self.window, 1), dd, dtype=np.float32)

        return np.concatenate([feats, pos, upnl_arr, dd_arr], axis=1)

    def step(self, action):
        price = float(self.df.loc[self.step_idx, "Close"])
        target = {0: 0.0, 1: 1.0, 2: -1.0}[int(action)]
        reward = 0.0
        done = False
        info = {}

        # Transaction cost on position change
        if target != self.position:
            cost = abs(target - self.position) * (self.commission + self.slippage)
            self.balance -= cost * self.balance
            if self.position != 0:
                pnl = (price / self.entry_price - 1) * self.position * self.balance
                self.balance += pnl
                self.returns.append(pnl / self.initial_balance)
            self.position = target
            self.entry_price = price

        # Mark-to-market
        upnl = 0.0
        if self.position != 0:
            upnl = (price / self.entry_price - 1) * self.position * self.balance
        self.equity = self.balance + upnl
        self.peak_equity = max(self.peak_equity, self.equity)
        self.equity_curve.append(self.equity)

        # ===== Sophisticated reward shaping =====
        step_ret = (self.equity - self.equity_curve[-2]) / self.initial_balance
        reward += step_ret * 10.0

        # Rolling Sharpe component
        if len(self.returns) > 20:
            recent = np.array(self.returns[-20:])
            sharpe = recent.mean() / (recent.std() + 1e-8)
            reward += 0.05 * sharpe

        # Asymmetric drawdown penalty
        dd = self.equity / self.peak_equity - 1
        if dd < -0.03:
            reward -= 0.5 * abs(dd)
        if dd < -self.max_dd_limit:
            reward -= 5.0
            done = True

        # Small holding cost
        reward -= 0.00005 * abs(self.position)

        # Bonus / penalty on closing trades
        if target != self.position and self.position != 0:
            reward += 0.1 if upnl > 0 else -0.15

        self.step_idx += 1
        if self.step_idx >= len(self.df) - 1:
            done = True

        obs = (
            self._get_obs()
            if not done
            else np.zeros(self.observation_space.shape, dtype=np.float32)
        )
        return obs, float(reward), done, False, info
