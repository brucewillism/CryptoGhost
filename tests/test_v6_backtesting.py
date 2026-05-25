"""Tests for v6 backtesting metrics."""

from backend.app.backtesting.metrics import compute_metrics


def test_compute_metrics_basic():
    returns = [0.01, -0.005, 0.02, 0.01, -0.01]
    pnls = [100, -50, 200, 100, -100]
    m = compute_metrics(returns, pnls, 3, 10)
    assert m.total_trades == 5
    assert 0 <= m.win_rate <= 1
    assert m.profit_factor >= 0
