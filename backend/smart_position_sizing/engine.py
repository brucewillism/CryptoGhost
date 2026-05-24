"""CryptoGhost v4 - Smart Position Sizing."""

from dataclasses import dataclass

from backend.investment.context import MarketContext
from backend.risk_reward_optimizer.engine import RiskRewardAssessment
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.smart_position_sizing")


@dataclass
class PositionSizing:
    symbol: str
    position_size_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    trailing_stop_pct: float
    max_loss_pct: float
    rationale: str


class SmartPositionSizingEngine:
    """Tamanho ideal de posição com stops adaptativos."""

    MAX_POSITION_PCT = 15.0
    MIN_POSITION_PCT = 0.5

    def calculate(
        self,
        ctx: MarketContext,
        rr: RiskRewardAssessment,
        kelly_override: float | None = None,
    ) -> PositionSizing:
        settings = get_settings()
        base_sl = settings.default_stop_loss_pct
        base_tp = settings.default_take_profit_pct

        kelly = kelly_override if kelly_override is not None else rr.kelly_fraction
        size = kelly * 100 * ctx.calibrated_confidence
        size *= ctx.liquidity_score
        size *= max(0.3, 1 - ctx.volatility / 150)

        regime_mult = {"bull_market": 1.1, "bear_market": 0.5, "high_volatility": 0.35, "sideways": 0.75}.get(ctx.regime_name, 0.8)
        size *= regime_mult

        if not rr.approved:
            size = min(size, 2.0)

        size = max(self.MIN_POSITION_PCT, min(self.MAX_POSITION_PCT, size))

        vol_adj = 1 + (ctx.volatility - 50) / 100
        stop_loss = max(0.5, min(5.0, base_sl * vol_adj))
        take_profit = max(1.0, min(15.0, base_tp * (1 + rr.sharpe_ratio * 0.1)))
        trailing = max(0.3, min(2.0, settings.trailing_stop_pct * vol_adj))

        avg_corr = sum(abs(v) for v in ctx.correlations.values()) / max(len(ctx.correlations), 1)
        if avg_corr > 0.7:
            size *= 0.7

        return PositionSizing(
            symbol=ctx.symbol,
            position_size_pct=round(size, 2),
            stop_loss_pct=round(stop_loss, 2),
            take_profit_pct=round(take_profit, 2),
            trailing_stop_pct=round(trailing, 2),
            max_loss_pct=round(size * stop_loss / 100, 4),
            rationale=f"Kelly={kelly:.3f}, regime={ctx.regime_name}, conf={ctx.calibrated_confidence:.2f}, approved={rr.approved}",
        )
