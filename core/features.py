"""
Advanced feature engineering for XAUUSD.
Educational / research use only.
"""

import numpy as np
import pandas as pd
import ta
import pywt
from hurst import compute_Hc


def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add a rich set of technical, statistical and session features."""
    df = df.copy()

    # ----- Trend -----
    df["sma_20"] = ta.trend.sma_indicator(df["Close"], 20)
    df["sma_50"] = ta.trend.sma_indicator(df["Close"], 50)
    df["sma_200"] = ta.trend.sma_indicator(df["Close"], 200)
    df["ema_12"] = ta.trend.ema_indicator(df["Close"], 12)
    df["ema_26"] = ta.trend.ema_indicator(df["Close"], 26)
    df["macd"] = ta.trend.macd_diff(df["Close"])
    df["adx"] = ta.trend.adx(df["High"], df["Low"], df["Close"], 14)

    # ----- Momentum -----
    df["rsi"] = ta.momentum.rsi(df["Close"], 14)
    df["stoch"] = ta.momentum.stoch(df["High"], df["Low"], df["Close"])
    df["cci"] = ta.trend.cci(df["High"], df["Low"], df["Close"], 20)
    df["williams_r"] = ta.momentum.williams_r(df["High"], df["Low"], df["Close"])

    # ----- Volatility -----
    df["bb_high"] = ta.volatility.bollinger_hband(df["Close"])
    df["bb_low"] = ta.volatility.bollinger_lband(df["Close"])
    df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["Close"]
    df["atr"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], 14)
    df["atr_pct"] = df["atr"] / df["Close"]

    # ----- Volume -----
    df["obv"] = ta.volume.on_balance_volume(df["Close"], df["Volume"])
    df["mfi"] = ta.volume.money_flow_index(df["High"], df["Low"], df["Close"], df["Volume"], 14)

    # ----- Price action -----
    df["body"] = (df["Close"] - df["Open"]) / df["Open"]
    df["range"] = (df["High"] - df["Low"]) / df["Open"]
    df["upper_shadow"] = (df["High"] - df[["Open", "Close"]].max(axis=1)) / df["Open"]
    df["lower_shadow"] = (df[["Open", "Close"]].min(axis=1) - df["Low"]) / df["Open"]

    # ----- Lags & rolling stats -----
    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"ret_{lag}"] = df["Close"].pct_change(lag)
        df[f"vol_{lag}"] = df["Close"].pct_change().rolling(lag).std()

    df["dist_sma20"] = (df["Close"] - df["sma_20"]) / df["sma_20"]
    df["dist_sma50"] = (df["Close"] - df["sma_50"]) / df["sma_50"]
    df["dist_sma200"] = (df["Close"] - df["sma_200"]) / df["sma_200"]

    # ----- Wavelet energy (detail level 1) -----
    def wavelet_d1(x):
        if len(x) < 16:
            return np.nan
        try:
            coeffs = pywt.wavedec(x, "db4", level=3)
            return float(np.sum(np.square(coeffs[1])))
        except Exception:
            return np.nan

    df["wavelet_d1"] = df["Close"].rolling(64).apply(wavelet_d1, raw=True)

    # ----- Hurst exponent -----
    def rolling_hurst(series, window=100):
        def _h(x):
            try:
                H, _, _ = compute_Hc(x, kind="price", simplified=True)
                return H
            except Exception:
                return np.nan
        return series.rolling(window).apply(_h, raw=True)

    df["hurst"] = rolling_hurst(df["Close"])

    # ----- Regime proxies -----
    df["vol_regime"] = (df["atr_pct"] > df["atr_pct"].rolling(100).quantile(0.75)).astype(int)
    df["trend_regime"] = (
        (df["sma_20"] > df["sma_50"]) & (df["sma_50"] > df["sma_200"])
    ).astype(int)

    # ----- Session / calendar effects (gold is highly session-sensitive) -----
    df["hour_sin"] = np.sin(2 * np.pi * df.index.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df.index.hour / 24)
    df["is_london"] = ((df.index.hour >= 7) & (df.index.hour < 16)).astype(int)
    df["is_ny"] = ((df.index.hour >= 12) & (df.index.hour < 21)).astype(int)
    df["is_asia"] = ((df.index.hour >= 0) & (df.index.hour < 8)).astype(int)
    df["is_friday"] = (df.index.dayofweek == 4).astype(int)

    # ----- Higher-order moments -----
    df["ret_skew_24"] = df["Close"].pct_change().rolling(24).skew()
    df["ret_kurt_24"] = df["Close"].pct_change().rolling(24).kurt()

    return df.dropna()
