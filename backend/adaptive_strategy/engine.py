"""CryptoGhost v3 - Adaptive Strategy Engine."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.adaptive_strategy")


@dataclass
class StrategyConfig:
    stop_loss_pct: float
    take_profit_pct: float
    max_exposure_pct: float
    position_size_pct: float
    confidence_threshold: float
    trailing_stop_pct: float
    max_orders_per_hour: int
    aggressiveness: str


@dataclass
class AdaptiveAdjustment:
    reason: str
    previous: dict
    adjusted: dict
    regime: str


class AdaptiveStrategyEngine:
    """Adapta estratégia automaticamente conforme regime e volatilidade."""

    BASE_CONFIG = StrategyConfig(
        stop_loss_pct=1.5, take_profit_pct=3.0, max_exposure_pct=10.0,
        position_size_pct=2.0, confidence_threshold=0.6, trailing_stop_pct=0.5,
        max_orders_per_hour=20, aggressiveness="moderate",
    )

    REGIME_ADJUSTMENTS = {
        "bull_market": {"stop_loss_pct": 2.0, "take_profit_pct": 4.0, "position_size_pct": 3.0, "confidence_threshold": 0.55, "aggressiveness": "aggressive"},
        "bear_market": {"stop_loss_pct": 1.0, "take_profit_pct": 2.0, "position_size_pct": 1.0, "max_exposure_pct": 5.0, "confidence_threshold": 0.75, "aggressiveness": "defensive"},
        "high_volatility": {"stop_loss_pct": 0.8, "take_profit_pct": 1.5, "position_size_pct": 0.5, "max_exposure_pct": 3.0, "confidence_threshold": 0.8, "max_orders_per_hour": 5, "aggressiveness": "minimal"},
        "sideways": {"stop_loss_pct": 1.2, "take_profit_pct": 2.0, "position_size_pct": 1.5, "confidence_threshold": 0.65, "aggressiveness": "conservative"},
        "accumulation": {"stop_loss_pct": 2.0, "take_profit_pct": 5.0, "position_size_pct": 2.5, "confidence_threshold": 0.6, "aggressiveness": "moderate"},
        "distribution": {"stop_loss_pct": 1.0, "take_profit_pct": 2.0, "position_size_pct": 1.0, "confidence_threshold": 0.7, "aggressiveness": "defensive"},
    }

    def __init__(self) -> None:
        self._current = self.BASE_CONFIG
        self._regime = "sideways"

    def adapt(self, regime: str, volatility: float, crash_probability: float = 0.0) -> AdaptiveAdjustment:
        previous = self._config_to_dict(self._current)
        self._regime = regime

        adjustments = dict(self.REGIME_ADJUSTMENTS.get(regime, {}))

        if volatility > 80:
            adjustments["position_size_pct"] = min(adjustments.get("position_size_pct", 2.0), 1.0)
            adjustments["max_exposure_pct"] = min(adjustments.get("max_exposure_pct", 10.0), 5.0)
        if crash_probability > 0.6:
            adjustments["confidence_threshold"] = 0.85
            adjustments["max_orders_per_hour"] = 3
            adjustments["aggressiveness"] = "minimal"

        self._current = self._apply_adjustments(adjustments)
        adjusted = self._config_to_dict(self._current)

        logger.info("strategy_adapted", regime=regime, aggressiveness=self._current.aggressiveness)

        return AdaptiveAdjustment(
            reason=f"Regime {regime}, vol={volatility:.1f}, crash_prob={crash_probability:.2f}",
            previous=previous, adjusted=adjusted, regime=regime,
        )

    @property
    def current_config(self) -> StrategyConfig:
        return self._current

    def _apply_adjustments(self, adj: dict) -> StrategyConfig:
        base = self._config_to_dict(self.BASE_CONFIG)
        base.update(adj)
        return StrategyConfig(**base)

    @staticmethod
    def _config_to_dict(config: StrategyConfig) -> dict:
        return {
            "stop_loss_pct": config.stop_loss_pct, "take_profit_pct": config.take_profit_pct,
            "max_exposure_pct": config.max_exposure_pct, "position_size_pct": config.position_size_pct,
            "confidence_threshold": config.confidence_threshold, "trailing_stop_pct": config.trailing_stop_pct,
            "max_orders_per_hour": config.max_orders_per_hour, "aggressiveness": config.aggressiveness,
        }
