# CryptoGhost Quant Platform v6

## Architecture

Modular quant layer under `backend/app/` using Strangler Fig pattern.
Legacy modules in `backend/` remain functional; v6 activates via feature flags.

## Feature Flags (.env)

```
CRYPTOGHOST_V6_ENABLED=true
CRYPTOGHOST_CONSENSUS_V3_ENABLED=true
CRYPTOGHOST_AUTO_INVEST_V2_ENABLED=true
CRYPTOGHOST_RISK_V2_ENABLED=true
CRYPTOGHOST_MIN_CALIBRATED_CONFIDENCE=0.65
CRYPTOGHOST_MIN_CONSENSUS_AGREEMENT=3
CRYPTOGHOST_SIGNAL_MAX_AGE_MINUTES=60
```

## Layers

| Layer | Path | Purpose |
|-------|------|---------|
| Data | `app/data/` | Collectors, cache, normalization |
| Features | `app/features/` | FeatureStoreService |
| Regime | `app/ai/regime/` | RegimeDetectionService + policies |
| Consensus | `app/ai/consensus_v3/` | FINAL_SCORE + hard rules |
| Meta Learning | `app/ai/meta_learning/` | Dynamic agent weights |
| Risk | `app/risk/` | RiskEngineV2 + PositionSizing |
| Auto Invest | `app/auto_invest/` | AutoInvestV2 + SignalFreshness |
| Trade Memory | `app/learning/trade_memory/` | Historical trade learning |
| Backtesting | `app/backtesting/` | Walk-forward + Monte Carlo |
| Quant ML | `app/ai/quant_models/` | RF/XGB ensemble |
| Self-Improving | `app/self_improving_v6/` | Adaptive thresholds |

## API v6

Prefix: `/api/v1/v6/`

- `GET /consensus/{symbol}`
- `GET /regime/{symbol}`
- `GET /agent-performance`
- `POST /auto-invest/run`
- `POST /backtest/run`
- `GET /backtest/runs`
- `GET /trade-memory`
- `GET /risk/heat`
- `GET /learning/metrics`
- `POST /analyze/{symbol}`

## Celery Queues

- `analysis` — full analysis + auto invest
- `market_scan` — universe scan
- `retraining` — self-improving v6
- `backtesting` — backtest runs

## Migration

```bash
alembic upgrade head
```

Creates migration `006_quant_v6_schema`.
