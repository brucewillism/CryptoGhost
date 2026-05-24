"""CryptoGhost v5 - Meta Learning Engine."""

from dataclasses import dataclass

import numpy as np

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.meta_learning_engine")

MODELS = [
    "LSTMForecaster", "XGBoost", "TemporalFusionTransformer", "MonteCarlo",
    "BayesianEnsemble", "PPO_RL", "DQN_RL", "GradientBoosting",
]


@dataclass
class ModelSelection:
    best_model: str
    market_regime: str
    historical_accuracy: float
    sharpe_ratio: float
    model_weights: dict[str, float]
    confidence_correction: float


class MetaLearningEngine:
    """Aprende qual modelo funciona melhor por regime de mercado."""

    def __init__(self) -> None:
        self._performance_history: dict[str, dict[str, list[float]]] = {}

    def record_outcome(self, model: str, regime: str, accuracy: float, sharpe: float = 0.0) -> None:
        self._performance_history.setdefault(regime, {}).setdefault(model, []).append(accuracy)
        if len(self._performance_history[regime][model]) > 200:
            self._performance_history[regime][model] = self._performance_history[regime][model][-200:]

    def select_best_model(self, regime: str, model_metrics: dict[str, dict] | None = None) -> ModelSelection:
        model_metrics = model_metrics or {}
        scores: dict[str, float] = {}

        for model in MODELS:
            hist = self._performance_history.get(regime, {}).get(model, [])
            hist_acc = float(np.mean(hist)) if hist else 0.5
            live = model_metrics.get(model, {})
            acc = live.get("accuracy", hist_acc)
            sharpe = live.get("sharpe", 0.0)
            regime_penalty = 0.8 if regime == "high_volatility" and model in ("LSTMForecaster", "PPO_RL") else 1.0
            scores[model] = (acc * 0.6 + min(1.0, max(0, sharpe / 3)) * 0.4) * regime_penalty

        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        weights = {m: round(s / total, 4) for m, s in scores.items()}

        best_acc = scores[best]
        correction = min(1.0, max(0.3, best_acc))

        return ModelSelection(
            best_model=best, market_regime=regime,
            historical_accuracy=round(best_acc, 4),
            sharpe_ratio=round(model_metrics.get(best, {}).get("sharpe", 0), 4),
            model_weights=weights, confidence_correction=round(correction, 4),
        )

    def build_metrics_from_forecast(self, investment_v4: dict | None) -> dict[str, dict]:
        if not investment_v4:
            return {}
        fc = investment_v4.get("ai_forecast", {})
        weights = fc.get("model_weights", {})
        pred = fc.get("predicted_return_pct", 0)
        return {
            "LSTMForecaster": {"accuracy": 0.55 + min(0.3, abs(pred) / 100), "sharpe": weights.get("lstm", 0) * 2},
            "XGBoost": {"accuracy": 0.58 + min(0.25, abs(pred) / 120), "sharpe": weights.get("gbm", 0) * 2},
            "MonteCarlo": {"accuracy": 0.52, "sharpe": 1.0},
            "BayesianEnsemble": {"accuracy": investment_v4.get("profit_probability", {}).get("profit_probability", 0.5)},
        }
