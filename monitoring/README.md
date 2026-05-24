# Monitoring & Observability

CryptoGhost includes institutional-grade observability out of the box.

## Stack

| Component | URL | Config |
|-----------|-----|--------|
| Prometheus | http://localhost:9090 | [`docker/prometheus/prometheus.yml`](../docker/prometheus/prometheus.yml) |
| Grafana | http://localhost:3000 | [`docker/grafana/provisioning/`](../docker/grafana/provisioning/) |
| API Metrics | http://localhost:8000/metrics | Prometheus client (FastAPI) |
| Health Checks | http://localhost:8000/health/full | Real connection validation |

**Grafana default credentials:** `admin` / `cryptoghost` (change in production)

## Health Endpoints

| Endpoint | Validates |
|----------|-----------|
| `GET /health` | App status, paper trading mode |
| `GET /health/db` | PostgreSQL + pgvector extension |
| `GET /health/redis` | Redis ping + latency |
| `GET /health/ollama` | Remote/local Ollama + model availability |
| `GET /health/celery` | Broker + worker count |
| `GET /health/full` | All checks + security config |

## Key Prometheus Metrics

### v1–v2
- `cryptoghost_api_requests_total`
- `cryptoghost_websocket_connections`
- `cryptoghost_trades_total`

### v3 Quant
- `cryptoghost_gpu_vram_mb`
- `cryptoghost_rl_reward`
- `cryptoghost_events_total`
- `cryptoghost_drift_score`
- `cryptoghost_calibration_error`

### v4 Investment
- `cryptoghost_investment_rankings_total`
- `cryptoghost_opportunity_score`

### v5 Self-Improving
- `cryptoghost_self_improvement_cycles_total`
- `cryptoghost_drift_retrain_triggers`
- `cryptoghost_survival_mode_active`

## Structured Logs

Startup logs use tagged prefixes:

```
[STARTUP] [DATABASE] [REDIS] [OLLAMA] [AI] [CELERY] [API] [FRONTEND]
```

Configured via `backend/shared/startup_log.py` and structlog.

## Optional: Sentry

```env
CRYPTOGHOST_SENTRY_DSN=https://your-sentry-dsn
```

## Alerting (Production)

Configure Grafana alert rules for:
- Daily loss limit approaching
- Celery worker offline
- Ollama unreachable
- Database connection failures
- Drift score above threshold
