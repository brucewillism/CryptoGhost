"""Configuração de testes CryptoGhost."""

import os

os.environ.setdefault("CRYPTOGHOST_ENV", "test")
os.environ.setdefault("CRYPTOGHOST_SECRET_KEY", "test-secret-key-min-32-characters-long")
os.environ.setdefault("CRYPTOGHOST_JWT_SECRET", "test-jwt-secret-min-32-characters-long")
os.environ.setdefault("CRYPTOGHOST_DATABASE_URL", "postgresql+asyncpg://cryptoghost:cryptoghost@localhost:5432/cryptoghost_test")
os.environ.setdefault("CRYPTOGHOST_DATABASE_URL_SYNC", "postgresql://cryptoghost:cryptoghost@localhost:5432/cryptoghost_test")
os.environ.setdefault("CRYPTOGHOST_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CRYPTOGHOST_PAPER_TRADING", "true")
os.environ.setdefault("CRYPTOGHOST_LIVE_TRADING_ENABLED", "false")
os.environ.setdefault("CRYPTOGHOST_ADMIN_USERNAME", "bruce")
os.environ.setdefault("CRYPTOGHOST_ADMIN_PASSWORD", "test-password")
os.environ.setdefault("CRYPTOGHOST_OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("CRYPTOGHOST_OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("CRYPTOGHOST_AI_PROVIDER_DEFAULT", "ollama")
os.environ.setdefault("CRYPTOGHOST_FINBERT_ENABLED", "false")

import numpy as np
import pandas as pd
import pytest

from backend.shared.config import get_settings

get_settings.cache_clear()


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 120
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.005)
    return pd.DataFrame({
        "open": prices * 0.999,
        "high": prices * 1.002,
        "low": prices * 0.998,
        "close": prices,
        "volume": np.random.uniform(100, 1000, n),
    })
