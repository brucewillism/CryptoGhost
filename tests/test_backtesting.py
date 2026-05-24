"""Testes de backtesting CryptoGhost."""

from decimal import Decimal

import numpy as np
import pandas as pd

from backend.backtesting.engine import BacktestEngine


def test_backtest_runs():
    np.random.seed(42)
    n = 200
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.01)
    df = pd.DataFrame(
        {"open": prices * 0.999, "high": prices * 1.002, "low": prices * 0.998, "close": prices, "volume": np.random.uniform(100, 1000, n)}
    )
    engine = BacktestEngine(initial_capital=Decimal("10000"))
    result = engine.run(df, "BTC/USDT")
    assert result.symbol == "BTC/USDT"
    assert result.initial_capital == Decimal("10000")
    report = engine.generate_report(result)
    assert "performance" in report
