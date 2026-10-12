"""
Data loading helpers (Yahoo Finance proxy for XAUUSD / Gold).
For production replace with broker API or high-quality tick data.
"""

import pandas as pd
import yfinance as yf


def fetch_xauusd(period: str = "2y", interval: str = "1h") -> pd.DataFrame:
    """
    Fetch historical gold data.
    GC=F is the continuous gold futures contract (good proxy for XAUUSD).
    """
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError("No data returned from Yahoo Finance")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="first")]
    return df
