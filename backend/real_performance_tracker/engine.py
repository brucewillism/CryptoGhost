"""CryptoGhost v5 - Real Performance Tracker."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.real_performance_tracker")


@dataclass
class PerformanceMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    cagr_pct: float
    hit_rate: float
    expected_vs_actual_pct: float
    alpha_pct: float
    total_return_pct: float


class RealPerformanceTracker:
    """Métricas institucionais de performance real."""

    def compute(
        self,
        equity_curve: list[float] | pd.Series,
        expected_returns: list[float] | None = None,
        benchmark_returns: pd.Series | None = None,
        predictions: list[bool] | None = None,
    ) -> PerformanceMetrics:
        eq = pd.Series(equity_curve) if not isinstance(equity_curve, pd.Series) else equity_curve
        if len(eq) < 2:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0)

        returns = eq.pct_change().dropna()
        mean_r = float(returns.mean())
        std_r = float(returns.std()) or 1e-6
        downside = returns[returns < 0]
        down_std = float(downside.std()) if len(downside) > 0 else std_r

        sharpe = (mean_r / std_r) * np.sqrt(252)
        sortino = (mean_r / down_std) * np.sqrt(252) if down_std > 0 else 0
        dd = float((eq / eq.cummax() - 1).min() * 100)
        total_ret = float((eq.iloc[-1] / eq.iloc[0] - 1) * 100)
        periods = len(eq) / 252
        cagr = ((eq.iloc[-1] / eq.iloc[0]) ** (1 / max(periods, 0.01)) - 1) * 100 if periods > 0 else total_ret

        hit = float(np.mean(predictions)) if predictions else 0.5
        exp_vs_act = 0.0
        if expected_returns and len(expected_returns) > 0:
            exp_vs_act = float(np.mean(expected_returns)) - total_ret

        alpha = 0.0
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            bench_ret = float(benchmark_returns.mean() * 252 * 100)
            alpha = total_ret - bench_ret

        return PerformanceMetrics(
            sharpe_ratio=round(sharpe, 4), sortino_ratio=round(sortino, 4),
            max_drawdown_pct=round(abs(dd), 2), cagr_pct=round(cagr, 2),
            hit_rate=round(hit, 4), expected_vs_actual_pct=round(exp_vs_act, 2),
            alpha_pct=round(alpha, 2), total_return_pct=round(total_ret, 2),
        )

    def from_trades(self, trades: list[dict], initial: float = 10000) -> PerformanceMetrics:
        equity = [initial]
        preds = []
        for t in trades:
            pnl = float(t.get("pnl", 0))
            equity.append(equity[-1] + pnl)
            preds.append(pnl > 0)
        return self.compute(equity, predictions=preds)
