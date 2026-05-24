"""CryptoGhost v3 - Ensemble Engine institucional."""

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ensemble_engine")

DECISION_TO_INT = {"SELL": 0, "HOLD": 1, "BUY": 2}
INT_TO_DECISION = {0: "SELL", 1: "HOLD", 2: "BUY"}


@dataclass
class AgentPrediction:
    agent: str
    decision: str
    confidence: float
    calibrated_confidence: float = 0.0


@dataclass
class EnsembleResult:
    final_decision: str
    meta_confidence: float
    stacking_weights: dict[str, float]
    agent_predictions: dict[str, dict]
    method: str


class EnsembleEngine:
    """Stacking + boosting + regime-aware dynamic weighting."""

    REGIME_WEIGHTS = {
        "bull_market": {"analyst": 1.2, "sentiment": 1.1, "risk": 0.8, "regime": 1.0, "portfolio": 0.9},
        "bear_market": {"analyst": 0.9, "sentiment": 1.0, "risk": 1.3, "regime": 1.1, "portfolio": 1.0},
        "high_volatility": {"analyst": 0.8, "sentiment": 0.9, "risk": 1.4, "regime": 1.2, "portfolio": 1.1},
        "sideways": {"analyst": 1.0, "sentiment": 0.9, "risk": 1.0, "regime": 1.0, "portfolio": 1.0},
    }

    def __init__(self) -> None:
        self._meta_model: LogisticRegression | None = None
        self._boost_model: GradientBoostingClassifier | None = None
        self._agent_accuracy: dict[str, float] = {}
        self._trained = False

    def train_meta_model(self, history: list[dict], outcomes: list[int]) -> None:
        if len(history) < 20:
            return
        X = self._build_feature_matrix(history)
        self._meta_model = LogisticRegression(max_iter=1000, solver="lbfgs")
        self._meta_model.fit(X, outcomes)
        self._boost_model = GradientBoostingClassifier(n_estimators=50, max_depth=3)
        self._boost_model.fit(X, outcomes)
        self._trained = True

    def predict(
        self,
        predictions: list[AgentPrediction],
        regime: str = "sideways",
        historical_accuracy: dict[str, float] | None = None,
    ) -> EnsembleResult:
        historical_accuracy = historical_accuracy or self._agent_accuracy
        regime_weights = self.REGIME_WEIGHTS.get(regime, self.REGIME_WEIGHTS["sideways"])

        agent_preds = {}
        weighted_votes = {"SELL": 0.0, "HOLD": 0.0, "BUY": 0.0}
        stacking_weights = {}

        for pred in predictions:
            conf = pred.calibrated_confidence or pred.confidence
            acc = historical_accuracy.get(pred.agent, 0.5)
            regime_mult = regime_weights.get(pred.agent, 1.0)
            weight = conf * acc * regime_mult
            stacking_weights[pred.agent] = round(weight, 4)
            agent_preds[pred.agent] = {"decision": pred.decision, "confidence": conf, "weight": weight}
            decision = pred.decision.upper()
            if decision not in weighted_votes:
                decision = "HOLD"
            weighted_votes[decision] += weight

        if self._trained and self._meta_model is not None:
            features = self._predictions_to_features(predictions)
            meta_pred = int(self._meta_model.predict([features])[0])
            meta_conf = float(max(self._meta_model.predict_proba([features])[0]))
            final = INT_TO_DECISION.get(meta_pred, "HOLD")
            method = "stacking"
        else:
            final = max(weighted_votes, key=weighted_votes.get)  # type: ignore
            total = sum(weighted_votes.values()) or 1
            meta_conf = weighted_votes[final] / total
            method = "dynamic_weighted_voting"

        return EnsembleResult(
            final_decision=final,
            meta_confidence=round(meta_conf, 4),
            stacking_weights=stacking_weights,
            agent_predictions=agent_preds,
            method=method,
        )

    def update_accuracy(self, agent: str, was_correct: bool) -> None:
        current = self._agent_accuracy.get(agent, 0.5)
        self._agent_accuracy[agent] = current * 0.9 + (1.0 if was_correct else 0.0) * 0.1

    @staticmethod
    def _build_feature_matrix(history: list[dict]) -> np.ndarray:
        rows = []
        for h in history:
            rows.append([
                h.get("analyst_conf", 0.5), h.get("risk_conf", 0.5),
                h.get("sentiment_conf", 0.5), h.get("regime_conf", 0.5),
                DECISION_TO_INT.get(h.get("analyst_dec", "HOLD"), 1),
                DECISION_TO_INT.get(h.get("risk_dec", "HOLD"), 1),
            ])
        return np.array(rows)

    @staticmethod
    def _predictions_to_features(predictions: list[AgentPrediction]) -> list[float]:
        agent_map = {p.agent: p for p in predictions}
        return [
            agent_map.get("analyst", AgentPrediction("analyst", "HOLD", 0.5)).confidence,
            agent_map.get("risk", AgentPrediction("risk", "HOLD", 0.5)).confidence,
            agent_map.get("sentiment", AgentPrediction("sentiment", "HOLD", 0.5)).confidence,
            agent_map.get("regime", AgentPrediction("regime", "HOLD", 0.5)).confidence,
            DECISION_TO_INT.get(agent_map.get("analyst", AgentPrediction("analyst", "HOLD", 0.5)).decision.upper(), 1),
            DECISION_TO_INT.get(agent_map.get("risk", AgentPrediction("risk", "HOLD", 0.5)).decision.upper(), 1),
        ]
