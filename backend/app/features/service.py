"""FeatureStoreService — persistência incremental de features."""

from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.data.collectors.binance_collector import BinanceCollector
from backend.app.data.normalization.normalizer import utc_now
from backend.app.features.calculators.technical import compute_all_features
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models_v6 import FEATURE_SCHEMA_VERSION, FeatureSnapshotRecord

logger = get_logger("cryptoghost.v6.features")


class FeatureStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.collector = BinanceCollector()

    async def get_or_compute(
        self,
        session: AsyncSession,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 200,
        *,
        persist: bool = True,
    ) -> dict[str, float]:
        """Retorna features; persiste snapshot se não existir recente."""
        cutoff = utc_now()
        recent = await session.execute(
            select(FeatureSnapshotRecord)
            .where(
                FeatureSnapshotRecord.symbol == symbol,
                FeatureSnapshotRecord.timeframe == timeframe,
                FeatureSnapshotRecord.schema_version == self.settings.feature_schema_version,
            )
            .order_by(FeatureSnapshotRecord.timestamp.desc())
            .limit(1)
        )
        row = recent.scalar_one_or_none()
        if row and (cutoff - row.timestamp).total_seconds() < self.settings.feature_store_ttl:
            return dict(row.features)

        df = self.collector.fetch_ohlcv(symbol, timeframe, limit)
        features = compute_all_features(df)
        if not features:
            return row.features if row else {}

        if persist:
            record = FeatureSnapshotRecord(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=utc_now(),
                features=features,
                schema_version=self.settings.feature_schema_version,
            )
            session.add(record)
            await session.flush()
            logger.info("features_persisted", symbol=symbol, count=len(features))

        return features

    async def get_features(self, session: AsyncSession, symbol: str, as_of: datetime | None = None) -> dict[str, float]:
        query = (
            select(FeatureSnapshotRecord)
            .where(FeatureSnapshotRecord.symbol == symbol)
            .order_by(FeatureSnapshotRecord.timestamp.desc())
            .limit(1)
        )
        if as_of:
            query = query.where(FeatureSnapshotRecord.timestamp <= as_of)
        result = await session.execute(query)
        row = result.scalar_one_or_none()
        return dict(row.features) if row else {}
