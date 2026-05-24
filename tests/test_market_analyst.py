"""Testes do Market AI Analyst."""

import numpy as np
import pandas as pd

from backend.market_ai_analyst.indicators import TechnicalIndicators


def test_technical_indicators_compute():
    np.random.seed(42)
    n = 100
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.005)
    df = pd.DataFrame({
        "open": prices * 0.999, "high": prices * 1.002,
        "low": prices * 0.998, "close": prices,
        "volume": np.random.uniform(100, 1000, n),
    })
    indicators = TechnicalIndicators.compute(df)
    assert 0 <= indicators.rsi <= 100
    assert indicators.sma_20 > 0
    assert indicators.support <= indicators.resistance


def test_indicators_to_dict():
    from backend.market_ai_analyst.indicators import TechnicalIndicatorSet
    ind = TechnicalIndicatorSet(
        rsi=45, macd=0.1, macd_signal=0.05, macd_hist=0.05,
        ema_12=100, ema_26=99, sma_20=98, sma_50=95, vwap=99,
        bb_upper=105, bb_lower=95, bb_mid=100, atr=2, obv=1000,
        fib_382=97, fib_618=93, support=90, resistance=110,
        volume_ratio=1.2, momentum=3.5,
    )
    d = TechnicalIndicators.to_dict(ind)
    assert "rsi" in d
    assert d["rsi"] == 45
