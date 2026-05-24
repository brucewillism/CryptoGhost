"""CryptoGhost v4 - Investment Prioritizer."""

from dataclasses import dataclass, asdict

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.investment_prioritizer")


@dataclass
class PriorityResult:
    symbol: str
    priority_score: float
    expected_return: float
    risk_score: float
    confidence: float
    recommendation: str
    profit_probability: float
    approved: bool
    reasons: list[str]
    risk_level: str


class InvestmentPrioritizer:
    """Priorizador central que consolida todos os engines."""

    RECOMMENDATIONS = [
        (90, "HIGH_PRIORITY_BUY"),
        (75, "STRONG_BUY"),
        (60, "MODERATE_BUY"),
        (45, "WATCH"),
        (0, "AVOID"),
    ]

    def prioritize(
        self,
        ctx: MarketContext,
        opportunity_score: float,
        expected_return: float,
        profit_probability: float,
        risk_reward_score: float,
        alpha_score: float,
        approved: bool,
        institutional_strength: float,
    ) -> PriorityResult:
        risk_score = min(100, ctx.crash_probability * 100 + ctx.volatility * 0.5 + (1 - ctx.liquidity_score) * 30)

        priority = (
            opportunity_score * 0.25
            + min(100, max(0, expected_return * 3)) * 0.20
            + profit_probability * 100 * 0.20
            + risk_reward_score * 0.15
            + alpha_score * 0.10
            + ctx.calibrated_confidence * 100 * 0.10
        )
        priority -= risk_score * 0.20
        priority = max(0, min(100, priority))

        if not approved:
            priority = min(priority, 40)
            recommendation = "AVOID"
        else:
            recommendation = "AVOID"
            for threshold, label in self.RECOMMENDATIONS:
                if priority >= threshold:
                    recommendation = label
                    break

        reasons = self._build_reasons(ctx, opportunity_score, institutional_strength, expected_return, approved)

        risk_level = "low" if risk_score < 30 else "moderate" if risk_score < 55 else "high"

        return PriorityResult(
            symbol=ctx.symbol,
            priority_score=round(priority, 2),
            expected_return=round(expected_return, 2),
            risk_score=round(risk_score, 2),
            confidence=round(ctx.calibrated_confidence, 4),
            recommendation=recommendation,
            profit_probability=round(profit_probability, 4),
            approved=approved,
            reasons=reasons,
            risk_level=risk_level,
        )

    @staticmethod
    def _build_reasons(ctx: MarketContext, opp_score: float, inst: float, exp_ret: float, approved: bool) -> list[str]:
        reasons = []
        if ctx.regime_name == "bull_market":
            reasons.append("Regime bullish detectado")
        if ctx.sentiment_score > 0.3:
            reasons.append("Sentimento positivo")
        elif ctx.sentiment_score < -0.3:
            reasons.append("Sentimento negativo — cautela")
        if inst > 0.6:
            reasons.append("Fluxo institucional elevado")
        if ctx.momentum > 5:
            reasons.append("Momentum forte")
        if exp_ret > 5:
            reasons.append(f"Retorno esperado {exp_ret:.1f}%")
        if opp_score >= 75:
            reasons.append("Score de oportunidade institucional")
        if ctx.crash_probability > 0.4:
            reasons.append("Risco de crash elevado")
        if not approved:
            reasons.append("Rejeitado pelo otimizador risco/retorno")
        if ctx.quant_v3 and ctx.quant_v3.get("similarity", {}).get("summary"):
            reasons.append(ctx.quant_v3["similarity"]["summary"])
        return reasons[:8] if reasons else ["Análise inconclusiva — aguardar mais dados"]

    def to_dict(self, result: PriorityResult) -> dict:
        return asdict(result)
