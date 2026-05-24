# CryptoGhost — Guia de Deploy

## Docker Compose (Produção)

1. Configure `.env` com secrets seguros (min. 32 chars)
2. Defina `CRYPTOGHOST_ENV=production`
3. Mantenha `CRYPTOGHOST_PAPER_TRADING=true` até validação completa

```bash
docker compose -f docker-compose.yml up -d --build
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

## GitHub Actions CI/CD

Pipeline em `.github/workflows/ci.yml`:
- Lint (ruff)
- Testes backend (pytest)
- Build frontend

## Backups

```bash
# Manual
python scripts/backup_db.py

# Cron (Linux)
0 3 * * * cd /path/to/CryptoGhost && python scripts/backup_db.py
```

## Monitoramento

- **Prometheus**: http://host:9090
- **Grafana**: http://host:3000 (admin/cryptoghost — altere em produção)
- **Sentry**: configure `CRYPTOGHOST_SENTRY_DSN`

## Checklist Pré-Live

- [ ] Backtesting com Sharpe > 1.0
- [ ] Paper trading por no mínimo 30 dias
- [ ] Limites de risco configurados
- [ ] Notificações webhook testadas
- [ ] Backup automático configurado
- [ ] Chaves API com permissões mínimas (sem saque)
- [ ] Declaração tributária compreendida
