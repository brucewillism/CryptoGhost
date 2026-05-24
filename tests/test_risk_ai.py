"""Testes do Risk AI."""

import numpy as np
import pandas as pd

from backend.risk_ai.detector import RiskAI


def test_risk_assessment():
    np.random.seed(42)
    n = 100
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.01)
    df = pd.DataFrame({
        "open": prices * 0.999, "high": prices * 1.002,
        "low": prices * 0.998, "close": prices,
        "volume": np.random.uniform(100, 1000, n),
    })
    risk = RiskAI().assess(df, buy_pressure=0.55, liquidity_score=70)
    assert risk.overall_risk in ("low", "medium", "high", "critical")
    assert 0 <= risk.crash_probability <= 1
    assert risk.confidence > 0
