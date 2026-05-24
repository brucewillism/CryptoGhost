# CryptoGhost — Arquitetura de Inteligência v2

## Sistema Multi-Agente

| Agente | Módulo | Peso no Consenso |
|--------|--------|------------------|
| Analyst AI | `market_ai_analyst` | 30% |
| Risk AI | `risk_ai` | 25% |
| Sentiment AI | `sentiment_engine` | 20% |
| Regime AI | `market_regime` | 15% |
| Portfolio AI | `portfolio_ai` | 10% |

## IA Explicável

Toda decisão passa por `explainable_ai` que gera:
- Lista de razões interpretáveis
- Feature importance normalizada
- SHAP values (quando shap disponível)
- Decision trace (4 etapas)
- Explicação textual em português

## Provider Abstraction

```
backend/shared/ai_providers/
├── ollama_provider.py   # Llama 3, DeepSeek, Mistral
├── openai_provider.py   # GPT-4o
├── claude_provider.py   # Claude 3.5
├── gemini_provider.py   # Gemini 1.5
└── factory.py
```

## Memória Semântica

`ai_memory` armazena decisões com embeddings via Ollama/OpenAI e permite recall por similaridade cosseno.

## Redis Streams

Eventos publicados em `cryptoghost:ai:events` para consumo WebSocket em tempo real.
