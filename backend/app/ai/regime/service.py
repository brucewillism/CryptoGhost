"""RegimeDetectionService v6 — detecção + políticas."""

from dataclasses import asdict

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.regime.policies import RegimePolicy, get_policy
from backend.app.core.types import MarketRegimeV6
from backend.app.data.collectors.binance_collector import BinanceCollector
from backend.app.data.normalization.normalizer import utc_now
from backend.market_regime.detector import MarketRegimeDetector
from backend.shared.logging_config import get_logger
from backend.shared.models_v6 import RegimeHistoryV6Record

logger = get_logger("cryptoghost.v6.regime")

_LEGACY_MAP = {
    "bull_market": MarketRegimeV6.TRENDING_BULL,
    "bear_market": MarketRegimeV6.TRENDING_BEAR,
    "sideways": MarketRegimeV6.RANGING,
    "high_volatility": MarketRegimeV6.HIGH_VOLATILITY,
    "low_volatility": MarketRegimeV6.LOW_VOLATILITY,
    "accumulation": MarketRegimeV6.ACCUMULATION,
    "distribution": MarketRegimeV6.DISTRIBUTION,
}


class RegimeDetectionService:
    def __init__(self) -> None:
        self.detector = MarketRegimeDetector()
        self.collector = BinanceCollector()

    def detect(self, df: pd.DataFrame, symbol: str, funding_rate: float | None = None) -> tuple[MarketRegimeV6, float, dict]:
        legacy = self.detector.detect(df, symbol)
        regime = _LEGACY_MAP.get(legacy.regime, MarketRegimeV6.RANGING)

        if funding_rate is not None and abs(funding_rate) > 0.001:
            if funding_rate > 0.0005 and legacy.volatility > 50:
                regime = MarketRegimeV6.DISTRIBUTION
            elif funding_rate < -0.0005:
                regime = MarketRegimeV6.ACCUMULATION

        policy = get_policy(regime)
        meta = {
            "legacy_regime": legacy.regime,
            "volatility": legacy.volatility,
            "trend_strength": legacy.trend_strength,
            "funding_rate": funding_rate,
            "policy": asdict(policy),
        }
        return regime, legacy.confidence, meta

    async def detect_and_persist(
        self,
        session: AsyncSession,
        symbol: str,
        df: pd.DataFrame | None = None,
    ) -> tuple[MarketRegimeV6, RegimePolicy, float]:
        if df is None:
            df = self.collector.fetch_ohlcv(symbol)
        funding = self.collector.fetch_funding_rate(symbol)
        regime, confidence, meta = self.detect(df, symbol, funding)
        policy = get_policy(regime)

        session.add(RegimeHistoryV6Record(
            symbol=symbol,
            regime=regime.value,
            confidence=confidence,
            policy_applied=meta.get("policy"),
            features={"volatility": meta.get("volatility"), "funding_rate": funding},
        ))
        logger.info("regime_detected", symbol=symbol, regime=regime.value, confidence=confidence)
        return regime, policy, confidence
