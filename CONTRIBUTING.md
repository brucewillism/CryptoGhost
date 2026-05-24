# Contributing to CryptoGhost

Thank you for your interest in contributing to CryptoGhost — an institutional-grade, self-improving quantitative AI platform.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (recommended)
- PostgreSQL 16 with pgvector
- Redis 7+

### Local Setup

```bash
git clone https://github.com/your-org/CryptoGhost.git
cd CryptoGhost

cp .env.example .env
# Edit .env with your local configuration

python start_dev.py
```

Alternative (full Docker):

```bash
python start_dev.py --all-docker
```

### Running Tests

```bash
# Backend unit & integration tests
pytest tests/ -v

# Full stack (requires running services)
python scripts/test_full_stack.py

# Security scan before commit
python scripts/scan_secrets.py

# Pre-release validation
python scripts/pre_release_check.py
```

## Project Structure

```
CryptoGhost/
├── backend/           # FastAPI, Celery, all AI/trading modules (v1–v5)
├── frontend/          # React dashboard (Vite + TypeScript)
├── docs/              # Architecture, API, deployment guides
├── docker/            # Dockerfiles, Prometheus, Grafana configs
├── infrastructure/    # Infrastructure documentation
├── monitoring/        # Observability documentation
├── scripts/           # Utilities, scanners, backtests
├── tests/             # Pytest suite
├── database/          # PostgreSQL init scripts
├── datasets/          # Sample datasets (raw data gitignored)
└── notebooks/         # Research notebooks (outputs gitignored)
```

## Development Guidelines

### Architecture Rules

1. **Never remove existing modules** — v1 through v5 must remain functional
2. **Add, don't replace** — new features extend the platform
3. **Paper trading default** — live trading requires explicit configuration
4. **All AI decisions must be explainable** — include reasoning metadata

### Code Style

**Python:**
```bash
pip install -r requirements-dev.txt
black backend/ tests/ scripts/
isort backend/ tests/ scripts/
flake8 backend/ tests/
mypy backend/shared/
```

**Frontend:**
```bash
cd frontend/dashboard
npm run lint
npm run format
```

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add portfolio survival emergency mode
fix: resolve Ollama model name resolution
docs: update health check documentation
test: add v5 dashboard integration tests
chore: update dependencies
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Run tests and secret scanner
4. Fill out the PR template completely
5. Request review — at least one approval required
6. Squash merge preferred

### Adding a New Module

1. Create module under `backend/<module_name>/`
2. Add SQLAlchemy models in `backend/shared/models_*.py` if needed
3. Create Alembic migration in `backend/alembic/versions/`
4. Hook into orchestrator pipeline if intelligence-related
5. Add API routes under `backend/api/routes/`
6. Add tests in `tests/`
7. Update CHANGELOG.md

## Testing Requirements

- All new features must include tests
- Existing tests must pass (`pytest tests/`)
- No decrease in coverage for critical paths (auth, risk, trading)

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/` for architectural changes
- Update `CHANGELOG.md` for every release

## Questions?

Open a [GitHub Discussion](../../discussions) or an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
