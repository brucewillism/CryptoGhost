"""CryptoGhost - Gestão de Risco."""

from dataclasses import dataclass
from decimal import Decimal

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.risk_management")


@dataclass
class RiskConfig:
    max_daily_loss_pct: float
    max_exposure_pct: float
    default_stop_loss_pct: float
    default_take_profit_pct: float
    trailing_stop_pct: float
    max_positions: int = 5
    max_orders_per_hour: int = 20


@dataclass
class PositionRisk:
    symbol: str
    entry_price: Decimal
    quantity: Decimal
    side: str
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    trailing_stop_pct: float | None = None
    highest_price: Decimal | None = None
    lowest_price: Decimal | None = None


class RiskManager:
    """
    Gerenciador de risco do CryptoGhost.

    Implementa:
    - Stop-loss / Take-profit
    - Trailing stop
    - Limite diário de perdas
    - Limite máximo de exposição
    - Circuit breaker
    - Proteção contra overtrading
    """

    def __init__(self, portfolio_value: Decimal = Decimal("10000")):
        self.settings = get_settings()
        self.config = RiskConfig(
            max_daily_loss_pct=self.settings.max_daily_loss_pct,
            max_exposure_pct=self.settings.max_exposure_pct,
            default_stop_loss_pct=self.settings.default_stop_loss_pct,
            default_take_profit_pct=self.settings.default_take_profit_pct,
            trailing_stop_pct=self.settings.trailing_stop_pct,
        )
        self.portfolio_value = portfolio_value
        self.daily_pnl = Decimal("0")
        self.total_exposure = Decimal("0")
        self.trading_halted = False
        self.circuit_breaker_active = False
        self.orders_this_hour = 0

    @property
    def max_daily_loss(self) -> Decimal:
        return self.portfolio_value * Decimal(str(self.config.max_daily_loss_pct / 100))

    @property
    def max_exposure(self) -> Decimal:
        return self.portfolio_value * Decimal(str(self.config.max_exposure_pct / 100))

    def calculate_stop_loss(self, entry_price: Decimal, side: str, pct: float | None = None) -> Decimal:
        pct = pct or self.config.default_stop_loss_pct
        multiplier = Decimal(str(pct / 100))
        if side == "buy":
            return entry_price * (1 - multiplier)
        return entry_price * (1 + multiplier)

    def calculate_take_profit(self, entry_price: Decimal, side: str, pct: float | None = None) -> Decimal:
        pct = pct or self.config.default_take_profit_pct
        multiplier = Decimal(str(pct / 100))
        if side == "buy":
            return entry_price * (1 + multiplier)
        return entry_price * (1 - multiplier)

    def calculate_position_size(self, entry_price: Decimal, risk_pct: float = 1.0) -> Decimal:
        """Position sizing baseado em risco percentual do portfolio."""
        risk_amount = self.portfolio_value * Decimal(str(risk_pct / 100))
        stop_distance = entry_price * Decimal(str(self.config.default_stop_loss_pct / 100))
        if stop_distance == 0:
            return Decimal("0")
        return risk_amount / stop_distance

    def update_trailing_stop(self, position: PositionRisk, current_price: Decimal) -> Decimal | None:
        """Atualiza trailing stop para posição."""
        if not position.trailing_stop_pct:
            return position.stop_loss

        trailing_pct = Decimal(str(position.trailing_stop_pct / 100))

        if position.side == "buy":
            if position.highest_price is None or current_price > position.highest_price:
                position.highest_price = current_price
            new_stop = position.highest_price * (1 - trailing_pct)
            if position.stop_loss is None or new_stop > position.stop_loss:
                position.stop_loss = new_stop
        else:
            if position.lowest_price is None or current_price < position.lowest_price:
                position.lowest_price = current_price
            new_stop = position.lowest_price * (1 + trailing_pct)
            if position.stop_loss is None or new_stop < position.stop_loss:
                position.stop_loss = new_stop

        return position.stop_loss

    def check_stop_conditions(self, position: PositionRisk, current_price: Decimal) -> str | None:
        """Verifica se stop-loss, take-profit ou trailing stop foram atingidos."""
        self.update_trailing_stop(position, current_price)

        if position.side == "buy":
            if position.stop_loss and current_price <= position.stop_loss:
                return "stop_loss"
            if position.take_profit and current_price >= position.take_profit:
                return "take_profit"
        else:
            if position.stop_loss and current_price >= position.stop_loss:
                return "stop_loss"
            if position.take_profit and current_price <= position.take_profit:
                return "take_profit"

        return None

    def can_open_position(self, exposure: Decimal) -> tuple[bool, str]:
        """Verifica se nova posição pode ser aberta."""
        if self.trading_halted:
            return False, "Trading desligado - circuit breaker ativo"

        if self.circuit_breaker_active:
            return False, "Circuit breaker ativo"

        if self.daily_pnl <= -self.max_daily_loss:
            self.trading_halted = True
            logger.error("daily_loss_limit_hit", daily_pnl=str(self.daily_pnl))
            return False, f"Limite diário de perda atingido: {self.daily_pnl}"

        if self.total_exposure + exposure > self.max_exposure:
            return False, f"Exposição máxima excedida: {self.total_exposure + exposure}"

        if self.orders_this_hour >= self.config.max_orders_per_hour:
            return False, "Limite de ordens por hora atingido (overtrading)"

        return True, "OK"

    def record_pnl(self, pnl: Decimal) -> None:
        self.daily_pnl += pnl
        if self.daily_pnl <= -self.max_daily_loss:
            self.activate_circuit_breaker("Limite diário de perda atingido")

    def activate_circuit_breaker(self, reason: str) -> None:
        self.circuit_breaker_active = True
        self.trading_halted = True
        logger.critical("circuit_breaker_activated", reason=reason)

    def reset_daily(self) -> None:
        self.daily_pnl = Decimal("0")
        self.orders_this_hour = 0
        if not self.settings.circuit_breaker_enabled:
            self.trading_halted = False
            self.circuit_breaker_active = False

    def get_status(self) -> dict:
        return {
            "daily_pnl": float(self.daily_pnl),
            "max_daily_loss": float(self.max_daily_loss),
            "total_exposure": float(self.total_exposure),
            "max_exposure": float(self.max_exposure),
            "trading_halted": self.trading_halted,
            "circuit_breaker_active": self.circuit_breaker_active,
            "orders_this_hour": self.orders_this_hour,
        }
