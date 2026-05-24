"""CryptoGhost v4 - Alpha Detection Engine."""

from dataclasses import dataclass

import numpy as np

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.alpha_detection")


@dataclass
class AlphaSignal:
    symbol: str
    alpha_score: float
    alpha_type: str
    expected_edge_pct: float
    rarity: str
    details: dict


class AlphaDetectionEngine:
    """Detecta oportunidades acima da média do mercado."""

    def detect(self, ctx: MarketContext, market_avg_score: float = 50.0) -> AlphaSignal:
        close = ctx.df["close"].astype(float)
        returns_20d = float(close.pct_change(20).iloc[-1]) if len(close) > 20 else 0
        vol = ctx.df["volume"].astype(float)
        vol_surge = float(vol.iloc[-1] / max(vol.tail(20).mean(), 1))

        score_edge = ctx.score - market_avg_score
        momentum_edge = ctx.momentum - 5
        undervalued = float(ctx.analysis.get("indicators", {}).get("rsi", 50)) < 35 and ctx.regime_name in ("accumulation", "bull_market")

        alpha_type = "momentum_institutional"
        if undervalued:
            alpha_type = "undervalued_asymmetry"
        elif vol_surge > 2 and ctx.momentum > 10:
            alpha_type = "volume_breakout"
        elif score_edge > 20:
            alpha_type = "relative_strength"

        alpha_score = (
            max(0, score_edge) * 1.5 + max(0, momentum_edge) * 2
            + (vol_surge - 1) * 10 + (20 if undervalued else 0)
        )
        alpha_score = min(100, max(0, alpha_score))

        expected_edge = returns_20d * 100 * 0.3 + score_edge * 0.2 + ctx.momentum * 0.5
        rarity = "rare" if alpha_score > 75 else "moderate" if alpha_score > 50 else "common"

        return AlphaSignal(
            symbol=ctx.symbol,
            alpha_score=round(alpha_score, 2),
            alpha_type=alpha_type,
            expected_edge_pct=round(expected_edge, 2),
            rarity=rarity,
            details={
                "score_edge": round(score_edge, 2),
                "vol_surge": round(vol_surge, 2),
                "returns_20d_pct": round(returns_20d * 100, 2),
                "undervalued": undervalued,
            },
        )
