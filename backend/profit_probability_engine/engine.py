"""CryptoGhost v4 - Profit Probability Engine."""

from dataclasses import dataclass

from backend.investment.context import MarketContext
from backend.opportunity_scoring.engine import OpportunityScore
from backend.predictive_profit_engine.engine import ProfitForecast
from backend.probabilistic_analysis.engine import ProbabilisticResult
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.profit_probability_engine")


@dataclass
class ProfitProbability:
    symbol: str
    profit_probability: float
    loss_probability: float
    expected_value_pct: float
    confidence: float
    factors: dict


class ProfitProbabilityEngine:
    """Probabilidade REAL de lucro combinando histórico, contexto e calibração."""

    def calculate(
        self,
        ctx: MarketContext,
        prob: ProbabilisticResult,
        forecast: ProfitForecast,
        opportunity: OpportunityScore,
        similarity_bullish_prob: float = 0.5,
    ) -> ProfitProbability:
        base_profit = prob.bullish_probability
        if forecast.expected_return_pct > 0:
            base_profit *= min(1.2, 1 + forecast.expected_return_pct / 100)
        else:
            base_profit *= max(0.5, 1 + forecast.expected_return_pct / 200)

        base_profit *= ctx.calibrated_confidence
        base_profit *= opportunity.opportunity_score / 100
        base_profit = 0.6 * base_profit + 0.4 * similarity_bullish_prob

        loss_prob = prob.bearish_probability * (1 + ctx.crash_probability)
        total = base_profit + loss_prob
        if total > 1:
            base_profit /= total
            loss_prob /= total

        ev = forecast.expected_return_pct * base_profit - forecast.drawdown_probable_pct * loss_prob * 0.5

        factors = {
            "bullish_prob": prob.bullish_probability,
            "calibrated_confidence": ctx.calibrated_confidence,
            "opportunity_score": opportunity.opportunity_score,
            "similarity_bullish": similarity_bullish_prob,
            "expected_return": forecast.expected_return_pct,
            "regime": ctx.regime_name,
        }

        return ProfitProbability(
            symbol=ctx.symbol,
            profit_probability=round(min(0.99, max(0.01, base_profit)), 4),
            loss_probability=round(min(0.99, max(0.01, loss_prob)), 4),
            expected_value_pct=round(ev, 2),
            confidence=round(ctx.calibrated_confidence * (1 - prob.uncertainty), 4),
            factors=factors,
        )
