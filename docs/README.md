# CryptoGhost Documentation

> Self-Improving Institutional Quantitative AI Platform — v5.0.0

## Guides

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System architecture overview |
| [Intelligence Architecture](intelligence_architecture.md) | Multi-agent v2 design |
| [AI Strategy](ai_strategy.md) | Local-first + premium hybrid AI |
| [API Reference](api.md) | REST & WebSocket endpoints |
| [Deploy](deploy.md) | Production deployment |
| [Paper Trading Tutorial](paper_trading_tutorial.md) | Safe testing guide |
| [Troubleshooting](troubleshooting.md) | Common issues |
| [Tax Guide BR](tax_guide_br.md) | Brazilian tax considerations |

## Infrastructure

| Document | Description |
|----------|-------------|
| [Infrastructure](../infrastructure/README.md) | Docker, database, Ollama |
| [Monitoring](../monitoring/README.md) | Prometheus, Grafana, health checks |

## Release

| Document | Description |
|----------|-------------|
| [CHANGELOG](../CHANGELOG.md) | Version history v1→v5 |
| [ROADMAP](../ROADMAP.md) | Future development |
| [CONTRIBUTING](../CONTRIBUTING.md) | How to contribute |
| [SECURITY](../SECURITY.md) | Security policy |
| [GitHub Release Guide](github_release.md) | Publish to GitHub |

## Version Modules

| Version | Modules | API Prefix |
|---------|---------|------------|
| v1 | Trading, Risk, AI Engine | `/api/v1/trading`, `/api/v1/risk` |
| v2 | 10 Intelligence modules | `/api/v1/intelligence` |
| v3 | 12 Quant modules | `/api/v1/quant` |
| v4 | 13 Investment modules | `/api/v1/investment` |
| v5 | 14 Self-Improving modules | `/api/v1/v5` |

## Analysis Pipeline

```
POST /api/v1/intelligence/analyze/{symbol}
  → v2 Multi-Agent
  → v3 Quant Pipeline
  → v4 Investment Prioritizer
  → v5 Self-Improving Engine
```
