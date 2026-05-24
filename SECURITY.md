# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 5.0.x   | :white_check_mark: |
| < 5.0   | :x:                |

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

If you discover a security issue, please report it responsibly:

1. Email the maintainer (replace with your contact) or use GitHub **Private Security Advisories**
2. Include: description, steps to reproduce, impact assessment, suggested fix
3. Allow **90 days** for remediation before public disclosure

We will acknowledge receipt within **48 hours** and provide a timeline for fixes.

## Security Principles

CryptoGhost is designed for **personal/family use on your own accounts**. Security is foundational:

### Secrets Management

- **Never commit** `.env`, API keys, JWT secrets, or passwords
- Use `.env.example` as template only — generate secrets with `openssl rand -hex 32`
- Run `python scripts/scan_secrets.py` before every release
- Rotate keys immediately if exposed

### Trading Safety

- **Paper trading is enabled by default** (`CRYPTOGHOST_PAPER_TRADING=true`)
- Live trading requires explicit opt-in: `LIVE_TRADING_ENABLED=true` + `PAPER_TRADING=false` + `ENV=production`
- Circuit breaker and daily loss limits are enforced server-side

### API Security

- JWT authentication on protected endpoints
- CORS restricted to configured origins
- Prompt injection protection in AI Router
- Rate limiting recommended for production deployments

### Infrastructure

- PostgreSQL credentials should be changed from defaults in production
- Redis should not be exposed publicly
- Ollama endpoints should be firewalled or VPN-only when remote
- Grafana/Prometheus should not be publicly accessible without auth

## Responsible Use

CryptoGhost is **not financial advice**. Users are solely responsible for:

- Compliance with local regulations (including tax obligations)
- Securing their exchange API keys (read-only keys recommended for analysis)
- Understanding risks of automated trading
- Operating only on accounts they own

## Dependency Security

- Run `pip audit` and `npm audit` regularly
- GitHub Dependabot is recommended for automated dependency updates
- CI runs tests on every pull request

## Data Privacy

- No telemetry is sent to third parties by default
- Sentry is opt-in via `CRYPTOGHOST_SENTRY_DSN`
- Market data stays in your PostgreSQL instance
- Data lake files are stored locally under `data/lake/` (gitignored)

## Hardening Checklist (Production)

- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS (reverse proxy: nginx/Traefik)
- [ ] Restrict network access to DB/Redis/Ollama
- [ ] Use read-only exchange API keys where possible
- [ ] Enable audit logging
- [ ] Set up backup for PostgreSQL
- [ ] Configure Sentry or equivalent monitoring
