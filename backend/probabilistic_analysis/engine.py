"""CryptoGhost v4 - Probabilistic Analysis."""

from dataclasses import dataclass

import numpy as np

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.probabilistic_analysis")


@dataclass
class ProbabilisticResult:
    symbol: str
    bullish_probability: float
    bearish_probability: float
    sideways_probability: float
    uncertainty: float
    method: str


class ProbabilisticAnalysisEngine:
    """Inferência Bayesiana combinando sinais técnicos, sentimento e regime."""

    PRIORS = {"bull_market": (0.55, 0.25, 0.20), "bear_market": (0.20, 0.55, 0.25), "sideways": (0.25, 0.25, 0.50), "high_volatility": (0.30, 0.40, 0.30)}

    def analyze(self, ctx: MarketContext) -> ProbabilisticResult:
        prior = self.PRIORS.get(ctx.regime_name, (0.33, 0.33, 0.34))
        p_bull, p_bear, p_side = prior

        score_signal = (ctx.score - 50) / 50
        p_bull *= 1 + score_signal * 0.5
        p_bear *= 1 - score_signal * 0.5

        sent = ctx.sentiment_score
        p_bull *= 1 + sent * 0.3
        p_bear *= 1 - sent * 0.3

        if ctx.decision == "BUY":
            p_bull *= 1.3
        elif ctx.decision == "SELL":
            p_bear *= 1.3
        else:
            p_side *= 1.2

        p_bull *= 1 - ctx.crash_probability * 0.5
        p_bear *= 1 + ctx.crash_probability * 0.3

        total = p_bull + p_bear + p_side
        p_bull, p_bear, p_side = p_bull / total, p_bear / total, p_side / total

        entropy = -sum(p * np.log(p + 1e-10) for p in [p_bull, p_bear, p_side])
        uncertainty = float(entropy / np.log(3))

        return ProbabilisticResult(
            symbol=ctx.symbol,
            bullish_probability=round(p_bull, 4),
            bearish_probability=round(p_bear, 4),
            sideways_probability=round(p_side, 4),
            uncertainty=round(uncertainty, 4),
            method="bayesian_inference",
        )
