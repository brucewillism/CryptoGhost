"""Backtesting metrics."""

from dataclasses import dataclass

import numpy as np


@dataclass
class BacktestMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    expectancy: float
    recovery_factor: float
    exposure_time_pct: float
    total_return_pct: float
    total_trades: int


def compute_metrics(
    returns: list[float],
    pnls: list[float],
    exposure_bars: int,
    total_bars: int,
) -> BacktestMetrics:
    if not returns:
        return BacktestMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    arr = np.array(returns)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = len(wins) / max(len(pnls), 1)
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / max(gross_loss, 0.01)
    expectancy = float(np.mean(pnls)) if pnls else 0

    std = float(np.std(arr)) or 1e-9
    sharpe = float(np.mean(arr) / std * np.sqrt(252))
    downside = arr[arr < 0]
    sortino_std = float(np.std(downside)) if len(downside) else 1e-9
    sortino = float(np.mean(arr) / sortino_std * np.sqrt(252))

    cumulative = np.cumprod(1 + arr)
    peak = np.maximum.accumulate(cumulative)
    dd = (cumulative - peak) / peak
    max_dd = float(abs(dd.min()) * 100) if len(dd) else 0

    total_return = float((cumulative[-1] - 1) * 100) if len(cumulative) else 0
    recovery = total_return / max(max_dd, 0.01)

    return BacktestMetrics(
        sharpe_ratio=round(sharpe, 4),
        sortino_ratio=round(sortino, 4),
        max_drawdown_pct=round(max_dd, 4),
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 4),
        expectancy=round(expectancy, 4),
        recovery_factor=round(recovery, 4),
        exposure_time_pct=round(exposure_bars / max(total_bars, 1) * 100, 2),
        total_return_pct=round(total_return, 4),
        total_trades=len(pnls),
    )
