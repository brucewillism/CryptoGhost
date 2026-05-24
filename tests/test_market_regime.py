"""Testes do Market Regime Detector."""

import numpy as np
import pandas as pd

from backend.market_regime.detector import MarketRegimeDetector


def test_regime_detection():
    np.random.seed(42)
    n = 150
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.008)
    df = pd.DataFrame({
        "open": prices * 0.999, "high": prices * 1.002,
        "low": prices * 0.998, "close": prices,
        "volume": np.random.uniform(100, 1000, n),
    })
    detector = MarketRegimeDetector()
    result = detector.detect(df, "BTC/USDT")
    assert result.regime in [
        "bull_market", "bear_market", "sideways", "high_volatility",
        "low_volatility", "accumulation", "distribution",
    ]
    assert 0 < result.confidence <= 1
    assert result.strategy_adjustment
