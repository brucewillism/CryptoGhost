"""CryptoGhost - Métricas Prometheus para IA."""

from prometheus_client import Counter, Gauge, Histogram

AI_PREDICTIONS_TOTAL = Counter(
    "cryptoghost_ai_predictions_total",
    "Total de previsões geradas pela IA",
    ["agent", "symbol", "decision"],
)

AI_CONFIDENCE_GAUGE = Gauge(
    "cryptoghost_ai_confidence",
    "Confiança média da IA por agente",
    ["agent"],
)

AI_ACCURACY_GAUGE = Gauge(
    "cryptoghost_ai_accuracy",
    "Acurácia histórica da IA",
    ["agent"],
)

AI_LATENCY = Histogram(
    "cryptoghost_ai_latency_seconds",
    "Latência de inferência da IA",
    ["agent"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

MARKET_REGIME_GAUGE = Gauge(
    "cryptoghost_market_regime",
    "Regime de mercado detectado (codificado)",
    ["symbol", "regime"],
)

SENTIMENT_SCORE_GAUGE = Gauge(
    "cryptoghost_sentiment_score",
    "Score de sentimento de mercado",
    ["source"],
)

AI_FALSE_POSITIVES = Counter(
    "cryptoghost_ai_false_positives_total",
    "Falsos positivos detectados",
    ["agent"],
)

WEBSOCKET_CONNECTIONS = Gauge(
    "cryptoghost_websocket_connections",
    "Conexões WebSocket ativas",
)

GPU_VRAM_GAUGE = Gauge("cryptoghost_gpu_vram_mb", "VRAM utilizada em MB", ["device"])
RL_REWARD_GAUGE = Gauge("cryptoghost_rl_reward", "Reward RL por episódio", ["algorithm", "symbol"])
EVENT_THROUGHPUT = Counter("cryptoghost_events_total", "Total de eventos processados", ["event_type"])
FEATURE_STORE_OPS = Counter("cryptoghost_feature_store_ops_total", "Operações feature store", ["operation"])
DRIFT_SCORE_GAUGE = Gauge("cryptoghost_drift_score", "Score de drift por agente", ["agent"])
CALIBRATION_ERROR = Gauge("cryptoghost_calibration_error", "Erro de calibração", ["agent"])

CONSENSUS_AGREEMENT = Gauge(
    "cryptoghost_ai_consensus_agreement",
    "Nível de concordância entre agentes IA",
    ["symbol"],
)

INVESTMENT_RANKING_SCORE = Gauge("cryptoghost_investment_priority_score", "Score de prioridade de investimento", ["symbol"])
OPPORTUNITY_SCORE_GAUGE = Gauge("cryptoghost_opportunity_score", "Score de oportunidade 0-100", ["symbol"])
PROFIT_PROBABILITY_GAUGE = Gauge("cryptoghost_profit_probability", "Probabilidade de lucro", ["symbol"])
EXPECTED_RETURN_GAUGE = Gauge("cryptoghost_expected_return_pct", "Retorno esperado %", ["symbol"])
RANKING_ACCURACY = Gauge("cryptoghost_ranking_accuracy", "Acurácia do ranking IA", ["period"])
RISK_EXPOSURE_GAUGE = Gauge("cryptoghost_risk_exposure_pct", "Exposição total %", ["portfolio"])

AI_TRUTH_SCORE = Gauge("cryptoghost_ai_truth_score", "Score de honestidade IA", ["symbol"])
DRIFT_V5_SCORE = Gauge("cryptoghost_drift_v5_score", "Drift v5 por modelo", ["model"])
PREDICTION_ACCURACY = Gauge("cryptoghost_prediction_accuracy", "Acurácia rolling de previsões", ["symbol"])
SURVIVAL_SCORE_GAUGE = Gauge("cryptoghost_survival_score", "Score de sobrevivência do portfólio")
SELF_IMPROVEMENT_COUNTER = Counter("cryptoghost_self_improvement_actions_total", "Ações de auto-melhoria")
ORDERFLOW_ANOMALY = Counter("cryptoghost_orderflow_anomalies_total", "Anomalias orderflow", ["type"])
STRATEGY_FITNESS = Gauge("cryptoghost_strategy_fitness", "Fitness da estratégia evoluída")

V6_FINAL_SCORE = Gauge("cryptoghost_v6_final_score", "FINAL_SCORE consensus v3", ["symbol"])
V6_SIGNALS_TOTAL = Counter("cryptoghost_v6_signals_total", "Sinais v6 gerados", ["classification", "can_execute"])
V6_BACKTEST_RUNS = Counter("cryptoghost_v6_backtest_runs_total", "Backtests v6 executados")
V6_AUTO_INVEST_BLOCKED = Counter("cryptoghost_v6_auto_invest_blocked_total", "Auto-invest bloqueado", ["reason"])
