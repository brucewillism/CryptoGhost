"""CryptoGhost v4 - Risk Reward Optimizer."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.investment.context import MarketContext
from backend.predictive_profit_engine.engine import ProfitForecast
from backend.profit_probability_engine.engine import ProfitProbability
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.risk_reward_optimizer")


@dataclass
class RiskRewardAssessment:
    symbol: str
    sharpe_ratio: float
    sortino_ratio: float
    var_95_pct: float
    cvar_95_pct: float
    kelly_fraction: float
    risk_reward_score: float
    approved: bool
    rejection_reasons: list[str]


class RiskRewardOptimizer:
    """Otimização Sharpe/Sortino/VaR/Kelly com filtros de segurança."""

    MIN_CONFIDENCE = 0.45
    MIN_LIQUIDITY = 0.25
    MAX_CRASH_PROB = 0.65
    MIN_RR_SCORE = 35.0

    def assess(
        self,
        ctx: MarketContext,
        forecast: ProfitForecast,
        profit_prob: ProfitProbability,
    ) -> RiskRewardAssessment:
        close = ctx.df["close"].astype(float)
        returns = close.pct_change().dropna()
        if len(returns) < 10:
            returns = pd.Series([0.001, -0.001, 0.002])

        mean_r = float(returns.mean())
        std_r = float(returns.std()) or 0.01
        downside = returns[returns < 0]
        down_std = float(downside.std()) if len(downside) > 0 else std_r

        sharpe = (mean_r / std_r) * np.sqrt(252) if std_r > 0 else 0
        sortino = (mean_r / down_std) * np.sqrt(252) if down_std > 0 else 0
        var_95 = float(np.percentile(returns, 5)) * 100
        cvar_95 = float(returns[returns <= np.percentile(returns, 5)].mean()) * 100 if len(returns) > 5 else var_95

        win_prob = profit_prob.profit_probability
        win_loss_ratio = forecast.upside_downside_ratio
        kelly = max(0, min(0.25, win_prob - (1 - win_prob) / max(win_loss_ratio, 0.1)))

        rr_score = (
            sharpe * 15 + sortino * 10 + forecast.expected_return_pct * 2
            - abs(var_95) * 0.5 - ctx.crash_probability * 30 + profit_prob.confidence * 20
        )
        rr_score = max(0, min(100, rr_score))

        rejections = []
        if profit_prob.confidence < self.MIN_CONFIDENCE:
            rejections.append("low_confidence")
        if ctx.liquidity_score < self.MIN_LIQUIDITY:
            rejections.append("low_liquidity")
        if ctx.crash_probability > self.MAX_CRASH_PROB:
            rejections.append("high_crash_risk")
        if ctx.risk.get("instability_score", 0) > 80:
            rejections.append("market_manipulation_risk")
        if rr_score < self.MIN_RR_SCORE:
            rejections.append("insufficient_risk_reward")
        if forecast.expected_return_pct < 0 and ctx.decision == "BUY":
            rejections.append("negative_expected_return")

        return RiskRewardAssessment(
            symbol=ctx.symbol,
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            var_95_pct=round(var_95, 2),
            cvar_95_pct=round(cvar_95, 2),
            kelly_fraction=round(kelly, 4),
            risk_reward_score=round(rr_score, 2),
            approved=len(rejections) == 0,
            rejection_reasons=rejections,
        )
