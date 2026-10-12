"""
Triple-barrier labeling + meta-labeling pipeline.
Based on López de Prado methodology.
Educational / research use only.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import xgboost as xgb
import lightgbm as lgb
import joblib


def get_daily_vol(close: pd.Series, span: int = 100) -> pd.Series:
    """Exponentially weighted volatility."""
    return close.pct_change().ewm(span=span).std()


def get_events(
    close: pd.Series,
    t_events: pd.DatetimeIndex,
    pt_sl: list = [1.8, 1.2],
    min_ret: float = 0.0005,
    vertical_bars: int = 12,
) -> pd.DataFrame:
    """Generate events for the triple-barrier method."""
    t1 = close.index.searchsorted(t_events + pd.Timedelta(hours=vertical_bars))
    t1 = t1[t1 < len(close.index)]
    t1 = pd.Series(close.index[t1], index=t_events[: len(t1)])

    trgt = get_daily_vol(close).loc[t_events]
    trgt = trgt[trgt > min_ret].dropna()

    side = pd.Series(1.0, index=trgt.index)  # overwritten later by primary model
    events = pd.concat({"t1": t1, "trgt": trgt, "side": side}, axis=1).dropna(subset=["t1"])
    return events


def apply_triple_barrier(
    close: pd.Series, events: pd.DataFrame, pt_sl: list = [1.8, 1.2]
) -> pd.DataFrame:
    """Apply profit-take, stop-loss and vertical barriers."""
    out = events.copy()
    pt = pt_sl[0] * out["trgt"]
    sl = -pt_sl[1] * out["trgt"]

    for loc, t1 in out["t1"].fillna(close.index[-1]).items():
        path = close[loc:t1]
        path = (path / close[loc] - 1) * out.loc[loc, "side"]
        out.loc[loc, "pt"] = (
            path[path > pt.loc[loc]].index.min() if (path > pt.loc[loc]).any() else pd.NaT
        )
        out.loc[loc, "sl"] = (
            path[path < sl.loc[loc]].index.min() if (path < sl.loc[loc]).any() else pd.NaT
        )

    out["t1"] = out[["t1", "pt", "sl"]].min(axis=1)
    out["ret"] = (close.loc[out["t1"]].values / close.loc[out.index].values - 1) * out["side"]
    out["bin"] = np.sign(out["ret"]).astype(int)
    return out


def meta_labeling_pipeline(
    df: pd.DataFrame,
    feature_cols: list,
    pt_sl: list = [1.8, 1.2],
    save_models: bool = True,
):
    """
    Full primary + meta-labeling pipeline.
    1. Primary model predicts side
    2. Triple-barrier labels generated with that side
    3. Meta-model predicts whether the trade should be taken
    """
    df = df.copy()
    primary_side = np.where(df["sma_20"] > df["sma_50"], 1, -1)
    df["primary_side"] = primary_side

    t_events = df.index[100:]
    events = get_events(df["Close"], t_events, pt_sl=pt_sl)
    events["side"] = df.loc[events.index, "primary_side"]

    labels = apply_triple_barrier(df["Close"], events, pt_sl=pt_sl)
    df = df.join(labels[["bin", "ret", "t1"]], how="left")

    # Meta-label: 1 if primary side was correct
    df["meta_label"] = ((df["bin"] == df["primary_side"]) & (df["bin"] != 0)).astype(int)

    meta_df = df.dropna(subset=["meta_label", "bin"])
    X_meta = meta_df[feature_cols]
    y_meta = meta_df["meta_label"]
    y_side = meta_df["primary_side"].map({-1: 0, 1: 1})

    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_meta)

    primary_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    meta_model = lgb.LGBMClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    tscv = TimeSeriesSplit(n_splits=4)
    fold_scores = []
    for fold, (tr, val) in enumerate(tscv.split(X_scaled)):
        primary_model.fit(X_scaled[tr], y_side.iloc[tr])
        meta_model.fit(X_scaled[tr], y_meta.iloc[tr])
        acc = accuracy_score(y_meta.iloc[val], meta_model.predict(X_scaled[val]))
        fold_scores.append(acc)
        print(f"Fold {fold + 1} Meta Accuracy: {acc:.3f}")

    # Final fit on all data
    primary_model.fit(X_scaled, y_side)
    meta_model.fit(X_scaled, y_meta)

    if save_models:
        joblib.dump(scaler, "meta_scaler.pkl")
        joblib.dump(primary_model, "primary_side_model.pkl")
        joblib.dump(meta_model, "meta_model.pkl")
        joblib.dump(feature_cols, "feature_cols.pkl")

    return scaler, primary_model, meta_model, meta_df, fold_scores
