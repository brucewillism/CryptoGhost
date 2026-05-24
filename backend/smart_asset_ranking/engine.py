"""CryptoGhost v4 - Smart Asset Ranking."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.smart_asset_ranking")


@dataclass
class RankedAsset:
    symbol: str
    rank: int
    composite_score: float
    expected_return_pct: float
    risk_score: float
    liquidity_score: float
    confidence: float
    alpha_score: float
    recommendation: str


class SmartAssetRankingEngine:
    """Ranking global inteligente multi-fator."""

    def rank(self, assets: list[dict]) -> list[RankedAsset]:
        scored = []
        for a in assets:
            composite = (
                a.get("priority_score", 0) * 0.30
                + a.get("opportunity_score", 0) * 0.20
                + a.get("profit_probability", 0) * 100 * 0.15
                + a.get("risk_reward_score", 0) * 0.15
                + a.get("alpha_score", 0) * 0.10
                + a.get("confidence", 0) * 100 * 0.10
            )
            composite -= a.get("risk_score", 0) * 0.15
            scored.append((composite, a))

        scored.sort(key=lambda x: -x[0])
        result = []
        for i, (comp, a) in enumerate(scored):
            rec = a.get("recommendation", "HOLD")
            result.append(RankedAsset(
                symbol=a["symbol"], rank=i + 1, composite_score=round(comp, 2),
                expected_return_pct=a.get("expected_return", 0), risk_score=a.get("risk_score", 50),
                liquidity_score=a.get("liquidity_score", 0.5), confidence=a.get("confidence", 0),
                alpha_score=a.get("alpha_score", 0), recommendation=rec,
            ))
        return result
