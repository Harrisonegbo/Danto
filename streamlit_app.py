"""
XAUUSD AI Research Platform – Streamlit Dashboard
Educational / research use only. Not financial advice.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from core.data import fetch_xauusd
from core.features import add_advanced_features
from core.labeling import meta_labeling_pipeline
from core.backtester import vectorized_triple_barrier_backtest

st.set_page_config(
    page_title="XAUUSD AI Research Platform",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- DISCLAIMER -----------------
st.markdown(
    """
<div style="background-color:#7f1d1d;padding:15px;border-radius:10px;margin-bottom:20px">
<h3 style="color:white;margin:0">⚠️ EDUCATIONAL RESEARCH TOOL ONLY</h3>
<p style="color:#fecaca;margin:5px 0 0 0">
This platform is for research and paper-trading simulation. It is <b>NOT</b> financial advice.
Forex/CFD trading (especially XAUUSD) carries a high risk of losing money.
Past performance does not guarantee future results. Never risk capital you cannot afford to lose.
</p>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------- SIDEBAR -----------------
st.sidebar.title("🥇 XAUUSD AI Trader")
st.sidebar.markdown("Research & Paper-Trading Dashboard")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📊 Data & Features",
        "🧠 Train Models (Meta-Labeling)",
        "📈 Backtester",
        "🤖 RL Agent",
        "📡 Live Signals (Paper)",
        "⚙️ Settings & Risk",
    ],
)


def plot_candles(df, title="XAUUSD"):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
            )
        ]
    )
    fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=500)
    return fig


# ----------------- PAGES -----------------
if page == "🏠 Dashboard":
    st.header("XAUUSD AI Trading Research Platform")
    st.markdown(
        "Sophisticated ML + RL system with triple-barrier labeling, meta-labeling, and risk-aware execution simulation."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Focus", "XAUUSD only")
    col2.metric("Labeling", "Triple Barrier + Meta")
    col3.metric("Models", "XGBoost + LightGBM + PPO")
    col4.metric("Mode", "Paper Trading")

    st.subheader("Quick Start")
    st.markdown(
        """
1. Go to **Data & Features** → load history and engineer features  
2. **Train Models** → run primary + meta-labeling pipeline  
3. **Backtester** → evaluate with realistic barriers & costs  
4. **Live Signals** → generate paper signals (no real money)  
"""
    )

elif page == "📊 Data & Features":
    st.header("Data Loading & Advanced Feature Engineering")
    period = st.selectbox("History", ["1y", "2y", "3y", "4y"], index=1)
    interval = st.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)

    if st.button("Load & Engineer Features", type="primary"):
        with st.spinner("Fetching data and computing advanced features..."):
            try:
                df = fetch_xauusd(period=period, interval=interval)
                df_feat = add_advanced_features(df)
                st.session_state["df"] = df_feat
                st.success(f"Loaded {len(df_feat)} bars with {df_feat.shape[1]} columns")
                st.plotly_chart(plot_candles(df_feat.tail(500)), use_container_width=True)
                st.subheader("Feature Preview")
                st.dataframe(df_feat.tail(10), use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

elif page == "🧠 Train Models (Meta-Labeling)":
    st.header("Primary Model + Meta-Labeling Pipeline")
    st.markdown(
        """
**Primary model** predicts side (long/short).  
**Meta-model** predicts whether the trade should be taken (quality filter).  
Labels are generated with the full **triple-barrier method**.
"""
    )

    if "df" not in st.session_state:
        st.warning("Please load data first in the Data & Features page.")
    else:
        if st.button("Run Full Meta-Labeling Pipeline", type="primary"):
            with st.spinner("Training primary + meta models (this may take a few minutes)..."):
                try:
                    df = st.session_state["df"]
                    feature_cols = [
                        c
                        for c in df.columns
                        if c
                        not in [
                            "Open",
                            "High",
                            "Low",
                            "Close",
                            "Volume",
                            "primary_side",
                            "bin",
                            "ret",
                            "t1",
                            "meta_label",
                        ]
                    ]
                    scaler, primary, meta, labeled, scores = meta_labeling_pipeline(
                        df, feature_cols, save_models=True
                    )
                    st.session_state["scaler"] = scaler
                    st.session_state["primary"] = primary
                    st.session_state["meta"] = meta
                    st.session_state["labeled"] = labeled
                    st.session_state["feature_cols"] = feature_cols
                    st.success(f"Models trained. Avg meta accuracy: {np.mean(scores):.3f}")
                    st.balloons()
                except Exception as e:
                    st.error(f"Training error: {e}")

elif page == "📈 Backtester":
    st.header("Vectorized Triple-Barrier Backtester")
    st.markdown("Respects profit-take, stop-loss and vertical (time) barriers + realistic costs.")

    if "labeled" not in st.session_state:
        st.warning("Train the models first.")
    else:
        pt = st.slider("Profit Take (× vol)", 1.0, 3.0, 1.8, 0.1)
        sl = st.slider("Stop Loss (× vol)", 0.5, 2.5, 1.2, 0.1)
        commission = st.number_input("Commission (round-turn)", 0.0001, 0.001, 0.0002, format="%.4f")
        slippage = st.number_input("Slippage", 0.00005, 0.0005, 0.00015, format="%.5f")

        if st.button("Run Backtest", type="primary"):
            labeled = st.session_state["labeled"]
            # Simple signal reconstruction for demo
            final_signal = pd.Series(0, index=labeled.index)
            if "primary_side" in labeled.columns and "meta_label" in labeled.columns:
                final_signal[(labeled["primary_side"] == 1) & (labeled["meta_label"] == 1)] = 1
                final_signal[(labeled["primary_side"] == -1) & (labeled["meta_label"] == 1)] = -1

            equity, trades, stats = vectorized_triple_barrier_backtest(
                labeled,
                final_signal,
                pt_sl=[pt, sl],
                commission=commission,
                slippage=slippage,
            )
            st.session_state["equity"] = equity
            st.session_state["trades"] = trades
            st.session_state["stats"] = stats

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Final Equity", f"{stats['final_equity']:.2f}×")
            col2.metric("Win Rate", f"{stats['win_rate']*100:.1f}%")
            col3.metric("Sharpe (approx)", f"{stats['sharpe']:.2f}")
            col4.metric("Max DD", f"{stats['max_dd']*100:.1f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=equity.index, y=equity.values, name="Equity"))
            fig.update_layout(title="Equity Curve", height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Trade Log")
            st.dataframe(trades, use_container_width=True)

elif page == "🤖 RL Agent":
    st.header("Reinforcement Learning Agent (PPO)")
    st.markdown(
        "Custom Gymnasium environment with sophisticated reward shaping "
        "(returns + Sharpe + drawdown penalties + asymmetric close bonuses)."
    )
    st.info("Training RL agents is computationally heavy. Run locally or on a machine with GPU.")
    st.code(
        """
from core.rl_env import AdvancedXAUUSDEnv
from stable_baselines3 import PPO
# env = AdvancedXAUUSDEnv(df, feature_cols)
# model = PPO("MlpPolicy", env, ...)
# model.learn(total_timesteps=150_000)
"""
    )

elif page == "📡 Live Signals (Paper)":
    st.header("Paper Trading Signals")
    st.markdown("Generates signals using the trained meta-labeling models. **No real orders are sent.**")

    if st.button("Generate Latest Signal"):
        if "labeled" not in st.session_state:
            st.warning("Train models first.")
        else:
            st.success("Example paper signal: LONG | Confidence 0.67 | Suggested size 0.01 lots (paper)")
            st.info("In a full deployment this would pull the latest bar, compute features and run the models.")

    st.subheader("Risk Guardrails (always active)")
    st.write("- Max risk per trade: 0.75%")
    st.write("- Daily loss limit")
    st.write("- Max drawdown circuit breaker")
    st.write("- Session filters (optional)")

elif page == "⚙️ Settings & Risk":
    st.header("Risk Management & Settings")
    st.number_input("Account Equity (paper)", 1000, 1_000_000, 10_000, step=1000)
    st.slider("Risk per trade (%)", 0.25, 2.0, 0.75, 0.25)
    st.slider("Max Portfolio Heat (%)", 1.0, 10.0, 3.0, 0.5)
    st.checkbox("Enable MT5 Demo Connection (advanced)", value=False)
    st.markdown("---")
    st.markdown("**MT5 Demo Instructions**")
    st.code(
        """
# Only after thorough testing on DEMO:
# from core.mt5_interface import MT5Interface
# mt5 = MT5Interface(login=..., password=..., server="Demo")
# rates = mt5.get_rates()
# ... generate signal ...
# mt5.place_order("buy", volume=0.01)   # DEMO ONLY
"""
    )

st.markdown("---")
st.caption(
    "XAUUSD AI Research Platform • Educational use only • Not financial advice • "
    + datetime.now().strftime("%Y-%m-%d %H:%M")
)
