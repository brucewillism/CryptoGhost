# CryptoGhost — Troubleshooting

## Backend não inicia

```bash
# Verifique variáveis obrigatórias
echo $CRYPTOGHOST_SECRET_KEY
echo $CRYPTOGHOST_DATABASE_URL

# Teste conexão PostgreSQL
docker compose ps postgres
```

## Erro de conexão com banco

```bash
docker compose up -d postgres
alembic -c backend/alembic.ini upgrade head
```

## Celery não processa tasks

```bash
docker compose logs celery-worker
redis-cli ping
```

## Dashboard não autentica

- Verifique `CRYPTOGHOST_ADMIN_USERNAME` e `CRYPTOGHOST_ADMIN_PASSWORD` no `.env`
- Confirme CORS: `CRYPTOGHOST_CORS_ORIGINS=http://localhost:5173`

## Rate limit da exchange

- CCXT usa `enableRateLimit: true` automaticamente
- Circuit breaker ativa após 5 falhas consecutivas
- Aguarde recovery timeout (60s)

## Trading real não funciona

Live trading requer **todas** as condições:

```
CRYPTOGHOST_ENV=production
CRYPTOGHOST_PAPER_TRADING=false
CRYPTOGHOST_LIVE_TRADING_ENABLED=true
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f celery-worker
```

Logs estruturados JSON em produção, console colorido em development.
