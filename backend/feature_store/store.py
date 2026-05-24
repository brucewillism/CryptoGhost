"""CryptoGhost v3 - Feature Store centralizado."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import redis as sync_redis
from sqlalchemy.orm import Session

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models_quant import FeatureVersionRecord

logger = get_logger("cryptoghost.feature_store")

CACHE_PREFIX = "cryptoghost:features"


class FeatureStore:
    """Online/offline feature store com versionamento, cache Redis e PostgreSQL."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis_url = settings.redis_url
        self._default_ttl = 300

    def _cache_key(self, name: str, symbol: str | None, version: int) -> str:
        sym = symbol or "global"
        return f"{CACHE_PREFIX}:{name}:{sym}:v{version}"

    def _get_redis(self) -> sync_redis.Redis:
        return sync_redis.from_url(self._redis_url, decode_responses=True)

    def get_latest_version(self, session: Session, feature_name: str, symbol: str | None = None) -> int:
        query = session.query(FeatureVersionRecord).filter(FeatureVersionRecord.feature_name == feature_name)
        if symbol:
            query = query.filter(FeatureVersionRecord.symbol == symbol)
        latest = query.order_by(FeatureVersionRecord.version.desc()).first()
        return latest.version if latest else 0

    def write(
        self,
        session: Session,
        feature_name: str,
        value: dict[str, Any],
        source: str,
        symbol: str | None = None,
        ttl_seconds: int | None = None,
        validate: bool = True,
    ) -> FeatureVersionRecord:
        if validate and not self._validate_features(value):
            raise ValueError(f"Feature validation failed for {feature_name}")

        version = self.get_latest_version(session, feature_name, symbol) + 1
        ttl = ttl_seconds or self._default_ttl

        record = FeatureVersionRecord(
            feature_name=feature_name,
            version=version,
            symbol=symbol,
            value=value,
            source=source,
            ttl_seconds=ttl,
            validated=validate,
        )
        session.add(record)
        session.flush()

        client = self._get_redis()
        try:
            cache_key = self._cache_key(feature_name, symbol, version)
            client.setex(cache_key, ttl, json.dumps(value, default=str))
            client.set(f"{CACHE_PREFIX}:latest:{feature_name}:{symbol or 'global'}", str(version), ex=ttl)
        finally:
            client.close()

        logger.debug("feature_written", name=feature_name, version=version, symbol=symbol)
        return record

    def read(
        self,
        session: Session,
        feature_name: str,
        symbol: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any] | None:
        client = self._get_redis()
        try:
            if version is None:
                latest_key = f"{CACHE_PREFIX}:latest:{feature_name}:{symbol or 'global'}"
                cached_version = client.get(latest_key)
                if cached_version:
                    cache_key = self._cache_key(feature_name, symbol, int(cached_version))
                    cached = client.get(cache_key)
                    if cached:
                        return json.loads(cached)
        finally:
            client.close()

        query = session.query(FeatureVersionRecord).filter(FeatureVersionRecord.feature_name == feature_name)
        if symbol:
            query = query.filter(FeatureVersionRecord.symbol == symbol)
        if version:
            query = query.filter(FeatureVersionRecord.version == version)
        record = query.order_by(FeatureVersionRecord.version.desc()).first()
        return record.value if record else None

    def read_batch(self, session: Session, feature_names: list[str], symbol: str) -> dict[str, Any]:
        return {name: self.read(session, name, symbol) for name in feature_names if self.read(session, name, symbol)}

    def ingest_technical_features(self, session: Session, symbol: str, indicators: dict) -> FeatureVersionRecord:
        return self.write(session, "technical_indicators", indicators, "market_ai_analyst", symbol, ttl_seconds=120)

    def ingest_sentiment_features(self, session: Session, sentiment: dict) -> FeatureVersionRecord:
        return self.write(session, "sentiment", sentiment, "sentiment_engine", ttl_seconds=180)

    def ingest_macro_features(self, session: Session, macro: dict) -> FeatureVersionRecord:
        return self.write(session, "macro", macro, "macro_analysis", ttl_seconds=600)

    @staticmethod
    def _validate_features(value: dict) -> bool:
        if not value:
            return False
        for k, v in value.items():
            if v is None:
                continue
            if isinstance(v, (int, float)) and (v != v or abs(v) > 1e15):
                return False
        return True

    def purge_expired(self, session: Session, older_than_days: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        count = session.query(FeatureVersionRecord).filter(FeatureVersionRecord.created_at < cutoff).delete()
        return count


_feature_store: FeatureStore | None = None


def get_feature_store() -> FeatureStore:
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store
