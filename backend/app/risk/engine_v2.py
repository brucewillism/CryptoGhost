"""Risk Engine V2 — exposure DB-backed + cooldown."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.risk_management.manager import RiskManager
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models import Order, Position

logger = get_logger("cryptoghost.v6.risk")


class RiskEngineV2:
    """Risk manager com estado persistente lido do banco."""

    def __init__(self, portfolio_value: Decimal | None = None) -> None:
        settings = get_settings()
        self.settings = settings
        pv = portfolio_value or Decimal(str(settings.paper_portfolio_usdt))
        self.manager = RiskManager(portfolio_value=pv)
        self._last_loss_at: float | None = None

    async def load_state(self, session: AsyncSession) -> None:
        pos_r = await session.execute(
            select(Position).where(Position.is_open == True)  # noqa: E712
        )
        positions = pos_r.scalars().all()
        exposure = Decimal("0")
        for p in positions:
            price = p.current_price or p.entry_price
            exposure += price * p.quantity
        self.manager.total_exposure = exposure

        orders_r = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(20)
        )
        recent = orders_r.scalars().all()
        self.manager.orders_this_hour = sum(
            1 for o in recent if o.status == "filled"
        )

    async def can_open(
        self,
        session: AsyncSession,
        exposure: Decimal,
        final_score: float,
    ) -> tuple[bool, str]:
        await self.load_state(session)

        if final_score < 50:
            return False, "Final score too low for any new position"

        can, reason = self.manager.can_open_position(exposure)
        if not can:
            return False, reason

        if self.manager.total_exposure + exposure > self.manager.max_exposure:
            return False, f"Portfolio heat exceeded: {self.manager.total_exposure + exposure}"

        return True, "OK"

    def calculate_stops(
        self,
        entry: Decimal,
        side: str,
        volatility_pct: float,
        policy_sl_mult: float = 1.0,
        policy_tp_mult: float = 1.0,
    ) -> tuple[Decimal, Decimal]:
        sl_pct = self.settings.default_stop_loss_pct * policy_sl_mult
        tp_pct = self.settings.default_take_profit_pct * policy_tp_mult
        if volatility_pct > 60:
            sl_pct *= 1.3
        return (
            self.manager.calculate_stop_loss(entry, side, sl_pct),
            self.manager.calculate_take_profit(entry, side, tp_pct),
        )

    def get_status(self) -> dict:
        return self.manager.get_status()
