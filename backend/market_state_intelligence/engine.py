"""CryptoGhost v5 - Market State Intelligence."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.market_state_intelligence")


@dataclass
class MarketState:
    symbol: str
    structural_state: str
    fragility_score: float
    hidden_risk_score: float
    trend_exhaustion: float
    manipulation_score: float
    details: dict


class MarketStateIntelligence:
    """Detecta estado estrutural oculto e fragilidade."""

    def analyze(self, df: pd.DataFrame, symbol: str, orderflow_spoofing: bool = False) -> MarketState:
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        returns = close.pct_change().dropna()
        vol = float(returns.std()) if len(returns) > 5 else 0.02
        vol_trend = float(volume.tail(5).mean() / max(volume.tail(20).mean(), 1))
        price_range = float((high.tail(20).max() - low.tail(20).min()) / close.iloc[-1])
        momentum = float(close.pct_change(10).iloc[-1]) if len(close) > 10 else 0

        higher_highs = sum(close.iloc[i] > close.iloc[i - 1] for i in range(-5, 0)) >= 3
        vol_declining = vol_trend < 0.8 and higher_highs
        exhaustion = min(1.0, max(0, (0.8 - vol_trend) * 2 + (0.5 if vol_declining else 0)))

        wick_asym = float(((high - close) / (high - low + 1e-10)).tail(10).mean())
        manipulation = min(1.0, wick_asym * 1.5 + (0.3 if orderflow_spoofing else 0))

        fragility = min(1.0, vol * 10 + (1 - vol_trend) * 0.3 + exhaustion * 0.4)
        hidden_risk = min(1.0, manipulation * 0.4 + fragility * 0.4 + (0.2 if momentum > 0.1 and vol_trend < 0.7 else 0))

        if hidden_risk > 0.7:
            state = "structurally_fragile"
        elif exhaustion > 0.6:
            state = "trend_exhaustion"
        elif manipulation > 0.5:
            state = "manipulation_risk"
        elif momentum > 0.05 and vol_trend > 1.2:
            state = "healthy_trend"
        else:
            state = "neutral_structure"

        return MarketState(
            symbol=symbol, structural_state=state,
            fragility_score=round(fragility, 4), hidden_risk_score=round(hidden_risk, 4),
            trend_exhaustion=round(exhaustion, 4), manipulation_score=round(manipulation, 4),
            details={
                "volatility": round(vol, 4), "volume_trend": round(vol_trend, 2),
                "momentum_10d": round(momentum * 100, 2), "price_range_pct": round(price_range * 100, 2),
            },
        )
