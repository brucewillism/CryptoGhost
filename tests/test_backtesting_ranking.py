"""Testes backtesting institucional com ranking."""

from decimal import Decimal

import numpy as np
import pandas as pd

from backend.backtesting.engine import BacktestEngine


def test_compare_ranking_backtest():
    np.random.seed(42)
    n = 100
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.005)
    df = pd.DataFrame({
        "open": prices * 0.999, "high": prices * 1.002,
        "low": prices * 0.998, "close": prices,
        "volume": np.random.uniform(100, 1000, n),
    })
    engine = BacktestEngine(initial_capital=Decimal("10000"))
    result = engine.compare_ranking_backtest(
        df, "BTC/USDT",
        [{"expected_return": 5.0, "profit_probability": 0.65}],
    )
    assert "ranking_validation" in result
    assert "prediction_error_pct" in result["ranking_validation"]
    assert "sharpe_ratio" in result["ranking_validation"]
