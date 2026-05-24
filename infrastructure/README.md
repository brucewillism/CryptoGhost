# Infrastructure

CryptoGhost infrastructure configuration and deployment assets.

## Layout

| Path | Description |
|------|-------------|
| [`../docker/`](../docker/) | Dockerfiles (backend, frontend) |
| [`../docker-compose.yml`](../docker-compose.yml) | Production-like full stack |
| [`../docker-compose.dev.yml`](../docker-compose.dev.yml) | Development stack (hot reload) |
| [`../database/`](../database/) | PostgreSQL init scripts (pgvector) |
| [`../start_dev.py`](../start_dev.py) | Intelligent dev startup script |

## Services

| Service | Port | Image |
|---------|------|-------|
| PostgreSQL + pgvector | 5432 | `pgvector/pgvector:pg16` |
| Redis | 6379 | `redis:7-alpine` |
| Ollama (optional local) | 11434 | `ollama/ollama:latest` |
| Backend API | 8000 | Custom (Python 3.12) |
| Frontend Dashboard | 5173 | Vite dev / nginx |
| Prometheus | 9090 | `prom/prometheus` |
| Grafana | 3000 | `grafana/grafana` |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

## Development

```bash
python start_dev.py              # Hybrid: Docker infra + local hot reload
python start_dev.py --all-docker # Full Docker dev stack
```

## Ollama — Local vs Remote

**Local** (default in `docker-compose.yml`):
```env
CRYPTOGHOST_OLLAMA_BASE_URL=http://localhost:11434
```

**Remote** (recommended for GPU servers):
```env
CRYPTOGHOST_OLLAMA_URL=http://your-ollama-host:11434
CRYPTOGHOST_OLLAMA_MODEL_PRIMARY=llama3.2:latest
```

See [Deploy Guide](../docs/deploy.md) for production hardening.
