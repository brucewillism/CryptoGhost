# Changelog

All notable changes to CryptoGhost are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [5.0.0] - 2026-05-24

### Release: CryptoGhost v5 — Self-Improving Institutional AI

#### Added — Self-Improving v5 (14 modules)
- Meta Learning Engine — model selection by market regime
- Self Improvement Engine — feedback loop, retraining, weight adjustment
- Institutional Data Lake — Parquet partitioned storage
- Orderflow AI — delta, absorption, spoofing detection
- Timing Optimization — probabilistic entry/exit
- Portfolio Survival — emergency mode, deleveraging
- Prediction Validation — continuous forecast vs reality
- Strategy Evolution — genetic algorithms
- Drift Detection v5 — PSI, concept drift, regime shift
- Real Performance Tracker — Sharpe, Sortino, CAGR, alpha
- AI Truth Engine — anti-overconfidence, probabilistic honesty
- Adaptive Weighting — dynamic weights by regime/accuracy
- Institutional Backtesting — slippage, spread, latency replay
- Market State Intelligence — structural fragility detection

#### Added — Infrastructure
- Health endpoints: `/health`, `/health/db`, `/health/redis`, `/health/ollama`, `/health/celery`, `/health/full`
- `start_dev.py` — intelligent dev startup script
- `docker-compose.dev.yml` — hot reload development stack
- `scripts/test_full_stack.py` — full stack integration tests
- Ollama remote support with retry, fallback, model resolution

#### Added — API
- `GET /api/v1/v5/dashboard` — Self-improving dashboard
- Celery task `run_self_improvement_cycle`

---

## [4.0.0] - 2026-05

### Release: Investment Intelligence v4

#### Added — Investment v4 (13 modules + AI Router)
- Investment Prioritizer, Opportunity Scoring, Predictive Profit Engine
- Risk Reward Optimizer, Capital Allocator, Institutional Signal Engine
- Smart Position Sizing, AI Forecast Engine, Probabilistic Analysis
- Adaptive Portfolio Engine, Alpha Detection, Profit Probability Engine
- Smart Asset Ranking, AI Router (Ollama + premium hybrid)

#### Added — API
- `GET /api/v1/investment/best-opportunity`
- `GET /api/v1/investment/dashboard`
- `GET /api/v1/investment/ranking`
- Investment Opportunity Dashboard (React)

---

## [3.0.0] - 2026-05

### Release: Institutional Quant Infrastructure v3

#### Added — Quant v3 (12 modules)
- Reinforcement Learning (DQN, PPO, SAC)
- Feature Store, Event Bus (Redis Streams)
- AI Calibration, Scenario Similarity (pgvector)
- GPU Inference, Ensemble Engine
- Temporal Memory, Adaptive Strategy
- Simulation Engine, AI Performance Lab, Market Replay Engine

#### Added — API
- `/api/v1/quant/*` endpoints
- Quant Institutional Dashboard

---

## [2.0.0] - 2026-05

### Release: Multi-Agent Intelligence Platform v2

#### Added — Intelligence v2 (10 modules)
- Multi-agent orchestrator (Market Analyst, Risk AI, Sentiment, Portfolio, Regime)
- Explainable AI (XAI), macro analysis, sentiment engine
- Market heatmap, consensus matrix, regime detection
- Intelligence API and dashboard panels

---

## [1.0.0] - 2026-05

### Release: Automated Trading Bot v1

#### Added — Core v1
- FastAPI backend with JWT authentication
- Paper trading (default) and live trading (opt-in)
- CCXT exchange integration (Binance, Bybit, Alpaca)
- Celery async tasks, Redis broker
- PostgreSQL + Alembic migrations
- React dashboard with WebSocket
- Risk management, circuit breaker
- Prometheus + Grafana observability

[5.0.0]: https://github.com/your-org/CryptoGhost/releases/tag/v5.0.0
[4.0.0]: https://github.com/your-org/CryptoGhost/releases/tag/v4.0.0
[3.0.0]: https://github.com/your-org/CryptoGhost/releases/tag/v3.0.0
[2.0.0]: https://github.com/your-org/CryptoGhost/releases/tag/v2.0.0
[1.0.0]: https://github.com/your-org/CryptoGhost/releases/tag/v1.0.0
