"""Regime policies — alteram pesos, risco e filtros por regime."""

from dataclasses import dataclass

from backend.app.core.types import MarketRegimeV6


@dataclass
class RegimePolicy:
    regime: MarketRegimeV6
    agent_weight_multiplier: dict[str, float]
    exposure_multiplier: float
    stop_loss_multiplier: float
    take_profit_multiplier: float
    min_final_score: float
    description: str = ""


DEFAULT_POLICIES: dict[MarketRegimeV6, RegimePolicy] = {
    MarketRegimeV6.TRENDING_BULL: RegimePolicy(
        MarketRegimeV6.TRENDING_BULL,
        {"analyst": 1.1, "sentiment": 1.0, "risk": 0.9, "regime": 1.1, "portfolio": 1.0},
        1.0, 1.0, 1.2, 55.0, "Trend bull — favor trend agents",
    ),
    MarketRegimeV6.TRENDING_BEAR: RegimePolicy(
        MarketRegimeV6.TRENDING_BEAR,
        {"analyst": 0.9, "sentiment": 1.1, "risk": 1.3, "regime": 1.1, "portfolio": 1.2},
        0.5, 0.8, 0.8, 70.0, "Bear — defensive, higher threshold",
    ),
    MarketRegimeV6.RANGING: RegimePolicy(
        MarketRegimeV6.RANGING,
        {"analyst": 1.0, "sentiment": 0.9, "risk": 1.0, "regime": 1.0, "portfolio": 1.0},
        0.7, 1.0, 1.0, 65.0, "Range — moderate exposure",
    ),
    MarketRegimeV6.HIGH_VOLATILITY: RegimePolicy(
        MarketRegimeV6.HIGH_VOLATILITY,
        {"analyst": 0.8, "sentiment": 0.8, "risk": 1.5, "regime": 1.2, "portfolio": 1.3},
        0.4, 0.7, 0.9, 75.0, "High vol — minimal exposure",
    ),
    MarketRegimeV6.LOW_VOLATILITY: RegimePolicy(
        MarketRegimeV6.LOW_VOLATILITY,
        {"analyst": 1.0, "sentiment": 1.0, "risk": 0.8, "regime": 0.9, "portfolio": 0.9},
        0.9, 1.1, 1.1, 58.0, "Low vol — normal sizing",
    ),
    MarketRegimeV6.ACCUMULATION: RegimePolicy(
        MarketRegimeV6.ACCUMULATION,
        {"analyst": 1.1, "sentiment": 1.0, "risk": 0.9, "regime": 1.0, "portfolio": 1.0},
        0.8, 1.2, 1.3, 60.0, "Accumulation — patient entries",
    ),
    MarketRegimeV6.DISTRIBUTION: RegimePolicy(
        MarketRegimeV6.DISTRIBUTION,
        {"analyst": 0.9, "sentiment": 1.2, "risk": 1.2, "regime": 1.1, "portfolio": 1.1},
        0.5, 0.8, 0.8, 72.0, "Distribution — reduce longs",
    ),
    MarketRegimeV6.NEWS_DRIVEN: RegimePolicy(
        MarketRegimeV6.NEWS_DRIVEN,
        {"analyst": 0.7, "sentiment": 1.4, "risk": 1.3, "regime": 0.9, "portfolio": 1.0},
        0.5, 0.9, 1.0, 68.0, "News driven — sentiment weighted",
    ),
}


def get_policy(regime: MarketRegimeV6) -> RegimePolicy:
    return DEFAULT_POLICIES.get(regime, DEFAULT_POLICIES[MarketRegimeV6.RANGING])
