"""Binance collector — wrap ExchangeConnector com cache e normalização."""

from typing import Any

import pandas as pd

from backend.app.data.cache.data_cache import DataCache
from backend.app.data.cache.rate_limiter import RateLimiter
from backend.app.data.normalization.normalizer import normalize_ohlcv, normalize_ticker
from backend.app.data.providers.retry import retry_with_backoff
from backend.data_collector.collector import ExchangeConnector


class BinanceCollector:
    def __init__(self, exchange: str = "binance") -> None:
        self.connector = ExchangeConnector(exchange)
        self.cache = DataCache(namespace="binance", default_ttl=60)
        self.limiter = RateLimiter(max_calls=8, period_seconds=1.0)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> pd.DataFrame:
        cache_key = f"ohlcv:{symbol}:{timeframe}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)

        def _fetch():
            self.limiter.wait_and_acquire()
            raw = self.connector.fetch_ohlcv(symbol, timeframe, limit)
            df = normalize_ohlcv(raw, symbol)
            self.cache.set(cache_key, df.to_dict(orient="list"), ttl=120)
            return df

        return retry_with_backoff(_fetch, max_retries=3)

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        cache_key = f"ticker:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        def _fetch():
            self.limiter.wait_and_acquire()
            ticker = self.connector.fetch_ticker(symbol)
            normalized = normalize_ticker(ticker, symbol)
            self.cache.set(cache_key, normalized, ttl=30)
            return normalized

        return retry_with_backoff(_fetch, max_retries=3)

    def fetch_order_book(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        self.limiter.wait_and_acquire()
        return self.connector.fetch_order_book(symbol, limit=limit)

    def fetch_funding_rate(self, symbol: str) -> float | None:
        try:
            self.limiter.wait_and_acquire()
            if hasattr(self.connector, "exchange") and self.connector.exchange:
                market = symbol.replace("/", "")
                fr = self.connector.exchange.fetch_funding_rate(symbol)
                return float(fr.get("fundingRate", 0))
        except Exception:
            return None
        return None
