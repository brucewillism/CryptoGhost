# CryptoGhost — Estratégia de IA

## Modelo Híbrido CryptoGhost-Hybrid-v1

### Por que este modelo?

| Componente | Peso | Justificativa |
|------------|------|---------------|
| LSTM (PyTorch) | 40% | Captura dependências temporais em séries de preços |
| Random Forest | 35% | Identifica relações não-lineares entre features OHLCV |
| Regras técnicas | 25% | Fallback interpretável (RSI, MACD) |

### Features

- OHLCV (open, high, low, close, volume)
- RSI-14, MACD, SMA-20/50, Bollinger Bands

### Sinais

- `buy`: tendência de alta prevista
- `sell`: tendência de baixa prevista
- `hold`: incerteza ou mercado lateral

### Métricas de Avaliação

| Métrica | Descrição |
|---------|-----------|
| Sharpe Ratio | Retorno ajustado ao risco (>1.5 = promissor) |
| Max Drawdown | Maior queda do pico (> -10% = revisar) |
| Win Rate | % de trades lucrativos |
| Acurácia RF | Precisão out-of-sample do Random Forest |

### Reinforcement Learning

A arquitetura suporta extensão com RL (estado = features de mercado, ação = buy/sell/hold, reward = PnL ajustado ao risco). Implementação futura recomendada via Stable-Baselines3 integrada ao `BacktestEngine`.

### Pipeline

1. Coleta de dados (Celery, 60s)
2. Feature engineering + indicadores
3. Inferência híbrida
4. Persistência em `ai_predictions`
5. Trading engine consome sinal se confiança > 0.6

### Treinamento

```bash
python scripts/train_ai.py --symbol BTC/USDT --output models/cryptoghost_hybrid.pt
```
