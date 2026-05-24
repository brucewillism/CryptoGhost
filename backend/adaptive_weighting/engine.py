"""CryptoGhost v5 - Adaptive Weighting Engine."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.adaptive_weighting")


@dataclass
class AgentWeights:
    weights: dict[str, float]
    regime: str
    rationale: str


class AdaptiveWeightingEngine:
    """Pesos dinâmicos por regime, acurácia e drawdown."""

    BASE = {"analyst": 1.0, "sentiment": 0.9, "risk": 1.1, "regime": 1.0, "portfolio": 0.95, "orderflow": 0.8}

    REGIME_MULT = {
        "bull_market": {"analyst": 1.2, "sentiment": 1.15, "risk": 0.85},
        "bear_market": {"risk": 1.4, "regime": 1.2, "analyst": 0.85},
        "high_volatility": {"risk": 1.5, "portfolio": 1.2, "analyst": 0.7},
        "sideways": {"regime": 1.1, "analyst": 1.0},
    }

    def compute(
        self,
        regime: str,
        agent_accuracy: dict[str, float] | None = None,
        drawdown_pct: float = 0,
        volatility: float = 50,
        self_improvement_weights: dict[str, float] | None = None,
    ) -> AgentWeights:
        agent_accuracy = agent_accuracy or {}
        si_weights = self_improvement_weights or {}
        weights = dict(self.BASE)

        for agent, mult in self.REGIME_MULT.get(regime, {}).items():
            weights[agent] = weights.get(agent, 1.0) * mult

        for agent in weights:
            acc = agent_accuracy.get(agent, 0.5)
            weights[agent] *= 0.7 + acc * 0.6
            weights[agent] *= si_weights.get(agent, 1.0)

        if drawdown_pct > 10:
            weights["risk"] *= 1.3
            weights["portfolio"] *= 1.2
        if volatility > 70:
            weights["risk"] *= 1.2

        total = sum(weights.values()) or 1
        normalized = {k: round(v / total * len(weights), 4) for k, v in weights.items()}

        return AgentWeights(
            weights=normalized, regime=regime,
            rationale=f"Regime={regime}, drawdown={drawdown_pct:.1f}%, vol={volatility:.0f}",
        )
