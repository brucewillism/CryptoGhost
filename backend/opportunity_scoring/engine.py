"""CryptoGhost v4 - Opportunity Scoring Engine."""

from dataclasses import dataclass

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.opportunity_scoring")

CLASSIFICATION = [
    (90, "institutional_opportunity"),
    (75, "strong_buy"),
    (60, "moderate_buy"),
    (40, "neutral"),
    (0, "avoid"),
]


@dataclass
class OpportunityScore:
    symbol: str
    opportunity_score: float
    classification: str
    components: dict


class OpportunityScoringEngine:
    """Score institucional 0-100 baseado em múltiplos fatores."""

    WEIGHTS = {
        "trend": 0.15,
        "volume": 0.10,
        "momentum": 0.12,
        "liquidity": 0.10,
        "volatility": 0.08,
        "sentiment": 0.12,
        "regime": 0.10,
        "institutional": 0.08,
        "macro": 0.08,
        "strength": 0.07,
    }

    def score(self, ctx: MarketContext, institutional_strength: float = 0.5) -> OpportunityScore:
        indicators = ctx.analysis.get("indicators", {})
        vol_ratio = float(indicators.get("volume_ratio", 1.0))
        rsi = float(indicators.get("rsi", 50))

        trend_score = min(100, max(0, ctx.score))
        volume_score = min(100, vol_ratio * 50)
        momentum_score = min(100, max(0, 50 + ctx.momentum * 5))
        liquidity_score = min(100, ctx.liquidity_score * 100)
        vol_penalty = max(0, 100 - ctx.volatility) if ctx.volatility > 70 else min(100, 50 + (50 - ctx.volatility))
        sentiment_score = min(100, (ctx.sentiment_score + 1) * 50)
        regime_score = {"bull_market": 85, "accumulation": 75, "sideways": 55, "bear_market": 30, "high_volatility": 25}.get(ctx.regime_name, 50)
        macro_score = 60.0
        if ctx.macro and ctx.macro.get("outlook"):
            outlook = str(ctx.macro["outlook"]).lower()
            macro_score = {"bullish": 80, "bearish": 30, "neutral": 55}.get(outlook, 55)
        strength_score = min(100, float(ctx.analysis.get("strength_score", 50)))
        inst_score = institutional_strength * 100

        components = {
            "trend": round(trend_score, 2),
            "volume": round(volume_score, 2),
            "momentum": round(momentum_score, 2),
            "liquidity": round(liquidity_score, 2),
            "volatility": round(vol_penalty, 2),
            "sentiment": round(sentiment_score, 2),
            "regime": round(regime_score, 2),
            "institutional": round(inst_score, 2),
            "macro": round(macro_score, 2),
            "strength": round(strength_score, 2),
            "rsi": rsi,
        }

        total = sum(components[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        classification = "avoid"
        for threshold, label in CLASSIFICATION:
            if total >= threshold:
                classification = label
                break

        return OpportunityScore(
            symbol=ctx.symbol,
            opportunity_score=round(min(100, max(0, total)), 2),
            classification=classification,
            components=components,
        )
