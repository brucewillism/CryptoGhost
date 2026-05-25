"""Tests for v6 data layer — cache fallback and normalizer."""

import pandas as pd

from backend.app.data.cache.data_cache import DataCache
from backend.app.data.normalization.normalizer import normalize_ohlcv, normalize_ticker


def test_data_cache_memory_fallback():
    DataCache.clear_memory()
    cache = DataCache(namespace="test", default_ttl=60)
    cache.set("key1", {"a": 1}, ttl=30)
    assert cache.get("key1") == {"a": 1}
    cache.delete("key1")
    assert cache.get("key1") is None


def test_normalize_ohlcv_from_list():
    raw = [[1700000000000, 100.0, 105.0, 99.0, 102.0, 1000.0]]
    df = normalize_ohlcv(raw, "BTC/USDT")
    assert len(df) == 1
    assert float(df.iloc[0]["close"]) == 102.0
    assert df.attrs["symbol"] == "BTC/USDT"


def test_normalize_ticker():
    ticker = normalize_ticker({"last": 50000, "bid": 49999, "ask": 50001}, "BTC/USDT")
    assert ticker["symbol"] == "BTC/USDT"
    assert ticker["last"] == 50000.0


def test_rate_limiter_acquire():
    from backend.app.data.cache.rate_limiter import RateLimiter

    limiter = RateLimiter(max_calls=100, period_seconds=1.0)
    limiter.wait_and_acquire()
    limiter.wait_and_acquire()
