# CryptoGhost — Tutorial Paper Trading

## Objetivo

Validar estratégias sem risco financeiro real.

## Passo a Passo

### 1. Confirmar modo paper

No `.env`:

```
CRYPTOGHOST_PAPER_TRADING=true
CRYPTOGHOST_LIVE_TRADING_ENABLED=false
```

### 2. Iniciar sistema

```bash
docker compose up -d
```

### 3. Acessar dashboard

- URL: http://localhost:5173
- Login: credenciais do `.env` (`CRYPTOGHOST_ADMIN_USERNAME/PASSWORD`)

### 4. Criar ordem demo via API

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"bruce","password":"sua-senha"}' | jq -r .access_token)

# Ordem paper
curl -X POST http://localhost:8000/api/v1/trading/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exchange":"binance","symbol":"BTC/USDT","side":"buy","quantity":"0.001"}'
```

### 5. Monitorar

- Dashboard: posições, ordens, sinal IA
- Logs: `GET /api/v1/dashboard/audit-logs`
- Risco: badge "PAPER TRADING" no header

### 6. Backtesting antes de operar

```bash
python scripts/run_backtest.py --symbol BTC/USDT
```

### 7. Critérios para considerar live

- Paper trading estável por 30+ dias
- Sharpe > 1.0 no backtesting
- Circuit breaker nunca acionado indevidamente
- Declaração tributária compreendida

**Nunca ative live trading sem confirmação explícita e consciência dos riscos.**
