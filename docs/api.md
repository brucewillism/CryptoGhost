# CryptoGhost — API v2 (Inteligência Financeira)

Base URL: `http://localhost:8000/api/v1`

## Endpoints de Inteligência (Novos)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/intelligence/analyze/{symbol}` | Análise completa multi-agente + XAI |
| GET | `/intelligence/analysis/{symbol}` | Última análise de ativo |
| GET | `/intelligence/consensus/{symbol}` | Consenso multi-agente |
| GET | `/intelligence/explanation/{symbol}` | Explicação XAI com SHAP |
| GET | `/intelligence/sentiment` | Sentimento de mercado |
| GET | `/intelligence/regime/{symbol}` | Regime de mercado |
| GET | `/intelligence/heatmap` | Heatmap de scores |
| GET | `/intelligence/macro` | Indicadores macro |
| GET | `/intelligence/news` | Análise de notícias |
| POST | `/intelligence/macro-news/analyze` | Executar análise macro + news |

## Resposta de Análise (Exemplo)

```json
{
  "symbol": "BTC/USDT",
  "analysis": {
    "score": 87,
    "trend": "bullish",
    "risk": "medium",
    "confidence": 0.84,
    "recommendation": "moderate_buy"
  },
  "consensus": {
    "final_decision": "BUY",
    "confidence": 0.82,
    "agreement": 4,
    "disagreement": 1
  },
  "explanation": {
    "decision": "BUY",
    "confidence": 0.82,
    "reasons": ["RSI oversold", "MACD bullish crossover", "High volume breakout"],
    "textual_explanation": "Decisão: BUY com confiança de 82%..."
  }
}
```

## Endpoints v1 (Mantidos)

Consulte rotas de `/auth`, `/trading`, `/ai`, `/dashboard`, `/risk` — inalteradas.

## WebSocket

`ws://localhost:8000/ws`

Eventos: `intelligence_update`, `sentiment_update`, `consensus_update`, `system_status`
