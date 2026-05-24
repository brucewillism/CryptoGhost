"""CryptoGhost v5 - Self Improvement Engine."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.self_improvement_engine")


@dataclass
class ImprovementAction:
    action_type: str
    target: str
    before_value: float
    after_value: float
    improvement_pct: float
    details: dict


class SelfImprovementEngine:
    """Loop de feedback contínuo com ajuste de pesos e redução de falsos positivos."""

    def __init__(self) -> None:
        self._agent_weights: dict[str, float] = {
            "analyst": 1.0, "sentiment": 1.0, "risk": 1.0, "regime": 1.0, "portfolio": 1.0,
        }
        self._false_positive_penalty = 0.05
        self._reward_rate = 0.03

    def process_feedback(
        self,
        validation_score: float,
        direction_correct: bool,
        false_positive: bool,
        drift_detected: bool,
    ) -> list[ImprovementAction]:
        actions: list[ImprovementAction] = []

        if false_positive:
            for agent in self._agent_weights:
                before = self._agent_weights[agent]
                self._agent_weights[agent] = max(0.3, before - self._false_positive_penalty)
                actions.append(ImprovementAction(
                    "weight_penalty", agent, before, self._agent_weights[agent],
                    round((self._agent_weights[agent] - before) / before * 100, 2),
                    {"reason": "false_positive"},
                ))

        if direction_correct and validation_score > 0.6:
            for agent in self._agent_weights:
                before = self._agent_weights[agent]
                self._agent_weights[agent] = min(1.5, before + self._reward_rate)
                actions.append(ImprovementAction(
                    "weight_reward", agent, before, self._agent_weights[agent],
                    round((self._agent_weights[agent] - before) / before * 100, 2),
                    {"reason": "correct_prediction"},
                ))

        if drift_detected:
            actions.append(ImprovementAction(
                "retrain_trigger", "ensemble", 0, 1, 0,
                {"reason": "drift_detected", "weights_reset_partial": True},
            ))
            for agent in self._agent_weights:
                self._agent_weights[agent] *= 0.95

        logger.info("self_improvement_applied", actions=len(actions))
        return actions

    @property
    def current_weights(self) -> dict[str, float]:
        return dict(self._agent_weights)

    def suggest_retraining(self, drift_score: float, threshold: float = 0.15) -> bool:
        return drift_score > threshold
