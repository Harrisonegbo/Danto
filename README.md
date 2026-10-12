# 🥇 XAUUSD AI Research Platform

**Educational / research tool only – NOT financial advice.**

A complete machine-learning + reinforcement-learning research platform focused exclusively on **XAUUSD (Gold)**.

## Features

- Advanced feature engineering (technical indicators, wavelets, Hurst exponent, session effects…)
- Full **triple-barrier labeling** (López de Prado style)
- **Meta-labeling** pipeline (primary side model + meta quality filter)
- Vectorized barrier-aware backtester with realistic costs
- PPO reinforcement-learning agent with sophisticated reward shaping
- MetaTrader 5 integration skeleton (demo only)
- **FastAPI** backend with JWT authentication
- SQLite storage for backtests and signal logs
- Real-time **WebSocket** paper-signal stream
- Simple modern HTML/JS frontend
- **Streamlit** research dashboard
- Docker support

## Quick Start

### 1. Local (recommended for development)

```bash
cd xauusd-ai-platform
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the website (FastAPI)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal – Streamlit dashboard
streamlit run streamlit_app.py
```

- Website: http://localhost:8000
- Streamlit: http://localhost:8501

### 2. Docker

```bash
docker-compose up --build
```

Open http://localhost:8000

## Project Structure

```
xauusd-ai-platform/
├── app/                  # FastAPI backend + static frontend
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models_db.py
│   └── static/
├── core/                 # ML / RL / data logic
│   ├── features.py
│   ├── labeling.py
│   ├── backtester.py
│   ├── rl_env.py
│   ├── data.py
│   └── mt5_interface.py
├── streamlit_app.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Important Disclaimers

- This software is for **education and research** only.
- It does **not** place real trades by default.
- Forex / CFD trading (especially gold) involves substantial risk of loss.
- Past performance (including any backtest) does not guarantee future results.
- Always paper-trade extensively and use proper risk management.
- Never risk capital you cannot afford to lose.
- The authors accept no liability for any losses incurred.

## Next Steps for Serious Research

1. Replace Yahoo Finance data with high-quality tick / 1-minute data.
2. Implement purged / embargoed cross-validation.
3. Add realistic XAUUSD spreads and swap costs.
4. Walk-forward the entire meta-labeling process.
5. Only after months of robust paper results consider a tiny demo live allocation.

---

Built for research purposes. Trade responsibly.
