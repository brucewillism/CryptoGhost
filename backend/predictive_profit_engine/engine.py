"""CryptoGhost v4 - Predictive Profit Engine."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.predictive_profit_engine")


@dataclass
class ProfitForecast:
    symbol: str
    expected_return_pct: float
    drawdown_probable_pct: float
    upside_downside_ratio: float
    horizon_days: int
    confidence_interval: dict
    method: str
    simulations: int


class PredictiveProfitEngine:
    """Previsão probabilística via Monte Carlo e análise de valor esperado."""

    def __init__(self, simulations: int = 2000):
        self.simulations = simulations

    def forecast(self, ctx: MarketContext, horizon_days: int = 14) -> ProfitForecast:
        close = ctx.df["close"].astype(float)
        returns = close.pct_change().dropna()
        if len(returns) < 20:
            mu, sigma = 0.0005, 0.02
        else:
            mu = float(returns.tail(60).mean())
            sigma = float(returns.tail(60).std())

        regime_adj = {"bull_market": 1.2, "bear_market": 0.7, "high_volatility": 0.85}.get(ctx.regime_name, 1.0)
        mu *= regime_adj
        sentiment_adj = 1.0 + (ctx.sentiment_score * 0.1)
        mu *= sentiment_adj

        rng = np.random.default_rng(42)
        paths = rng.normal(mu, sigma, (self.simulations, horizon_days))
        cumulative = np.cumprod(1 + paths, axis=1)
        final_returns = (cumulative[:, -1] - 1) * 100

        expected = float(np.mean(final_returns))
        p5, p95 = float(np.percentile(final_returns, 5)), float(np.percentile(final_returns, 95))
        drawdowns = []
        for path in cumulative:
            peak = np.maximum.accumulate(path)
            dd = (path - peak) / peak
            drawdowns.append(float(dd.min()) * 100)
        probable_dd = float(np.percentile(drawdowns, 25))

        upside = float(np.mean(final_returns[final_returns > 0])) if (final_returns > 0).any() else 0.01
        downside = abs(float(np.mean(final_returns[final_returns < 0]))) if (final_returns < 0).any() else 0.01
        ratio = upside / max(downside, 0.01)

        return ProfitForecast(
            symbol=ctx.symbol,
            expected_return_pct=round(expected, 2),
            drawdown_probable_pct=round(abs(probable_dd), 2),
            upside_downside_ratio=round(ratio, 2),
            horizon_days=horizon_days,
            confidence_interval={"p5": round(p5, 2), "p50": round(float(np.median(final_returns)), 2), "p95": round(p95, 2)},
            method="monte_carlo",
            simulations=self.simulations,
        )
