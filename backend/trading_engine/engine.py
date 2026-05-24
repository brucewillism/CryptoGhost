"""CryptoGhost - Engine de Execução de Trading."""

import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.audit_logs.service import AuditService
from backend.risk_management.manager import RiskManager
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models import Order, OrderSide, OrderStatus, OrderType, Position, TradingMode

logger = get_logger("cryptoghost.trading_engine")


class OrderRequest:
    """Request de ordem normalizada."""

    def __init__(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        trailing_stop_pct: float | None = None,
    ):
        self.exchange = exchange
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop_pct = trailing_stop_pct


class BaseExecutor(ABC):
    """Interface base para executores de ordens."""

    @abstractmethod
    async def place_order(self, request: OrderRequest) -> dict:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        pass

    @abstractmethod
    async def modify_order(self, order_id: str, symbol: str, params: dict) -> dict:
        pass


class PaperTradingExecutor(BaseExecutor):
    """Executor de paper trading para demo e testes."""

    def __init__(self):
        self.settings = get_settings()
        self._simulated_prices: dict[str, Decimal] = {}

    async def place_order(self, request: OrderRequest) -> dict:
        fill_price = request.price or self._get_simulated_price(request.symbol)
        external_id = f"PAPER-{uuid.uuid4().hex[:12]}"

        logger.info(
            "paper_order_placed",
            symbol=request.symbol,
            side=request.side.value,
            quantity=str(request.quantity),
            price=str(fill_price),
        )

        return {
            "external_id": external_id,
            "status": OrderStatus.FILLED.value,
            "filled_quantity": request.quantity,
            "average_price": fill_price,
            "trading_mode": TradingMode.PAPER.value,
        }

    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        logger.info("paper_order_cancelled", order_id=order_id, symbol=symbol)
        return {"order_id": order_id, "status": OrderStatus.CANCELLED.value}

    async def modify_order(self, order_id: str, symbol: str, params: dict) -> dict:
        logger.info("paper_order_modified", order_id=order_id, params=params)
        return {"order_id": order_id, "status": OrderStatus.OPEN.value, **params}

    def _get_simulated_price(self, symbol: str) -> Decimal:
        defaults = {"BTC/USDT": Decimal("65000"), "ETH/USDT": Decimal("3500"), "SOL/USDT": Decimal("150")}
        return self._simulated_prices.get(symbol, defaults.get(symbol, Decimal("100")))

    def set_simulated_price(self, symbol: str, price: Decimal) -> None:
        self._simulated_prices[symbol] = price


class LiveTradingExecutor(BaseExecutor):
    """Executor para trading real via CCXT - requer confirmação explícita."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.is_live_trading_allowed:
            raise RuntimeError(
                "Trading real desabilitado. Configure CRYPTOGHOST_LIVE_TRADING_ENABLED=true "
                "e CRYPTOGHOST_PAPER_TRADING=false em ambiente production."
            )

    async def place_order(self, request: OrderRequest) -> dict:
        from backend.data_collector.collector import ExchangeConnector

        connector = ExchangeConnector(request.exchange)
        exchange = connector._get_exchange()

        side = request.side.value
        order_type = "market" if request.order_type == OrderType.MARKET else "limit"

        params: dict[str, Any] = {}
        if request.stop_loss:
            params["stopLossPrice"] = float(request.stop_loss)
        if request.take_profit:
            params["takeProfitPrice"] = float(request.take_profit)

        result = exchange.create_order(
            request.symbol,
            order_type,
            side,
            float(request.quantity),
            float(request.price) if request.price else None,
            params,
        )

        logger.info("live_order_placed", symbol=request.symbol, external_id=result["id"])
        return {
            "external_id": result["id"],
            "status": result.get("status", OrderStatus.OPEN.value),
            "filled_quantity": Decimal(str(result.get("filled", 0))),
            "average_price": Decimal(str(result.get("average", 0))) if result.get("average") else None,
            "trading_mode": TradingMode.LIVE.value,
        }

    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        raise NotImplementedError("Use TradingEngine.cancel_order com exchange context")

    async def modify_order(self, order_id: str, symbol: str, params: dict) -> dict:
        raise NotImplementedError("Use TradingEngine.modify_order com exchange context")


class TradingEngine:
    """Engine principal de execução do CryptoGhost."""

    def __init__(self, risk_manager: RiskManager | None = None):
        self.settings = get_settings()
        self.risk_manager = risk_manager or RiskManager()
        self.executor: BaseExecutor = (
            PaperTradingExecutor() if self.settings.paper_trading else LiveTradingExecutor()
        )

    async def execute_order(
        self,
        session: AsyncSession,
        request: OrderRequest,
        actor: str = "system",
    ) -> Order:
        """Executa ordem com validação de risco e auditoria."""
        exposure = request.quantity * (request.price or Decimal("1"))
        can_trade, reason = self.risk_manager.can_open_position(exposure)

        if not can_trade:
            logger.warning("order_rejected", reason=reason, symbol=request.symbol)
            order = Order(
                exchange=request.exchange,
                symbol=request.symbol,
                side=request.side.value,
                order_type=request.order_type.value,
                status=OrderStatus.REJECTED.value,
                quantity=request.quantity,
                price=request.price,
                metadata_={"rejection_reason": reason},
                trading_mode=TradingMode.PAPER.value if self.settings.paper_trading else TradingMode.LIVE.value,
            )
            session.add(order)
            await AuditService.log_decision(session, "order_rejected", {"reason": reason, "symbol": request.symbol})
            return order

        if not request.stop_loss:
            request.stop_loss = self.risk_manager.calculate_stop_loss(
                request.price or Decimal("1"), request.side.value
            )
        if not request.take_profit:
            request.take_profit = self.risk_manager.calculate_take_profit(
                request.price or Decimal("1"), request.side.value
            )
        if not request.trailing_stop_pct:
            request.trailing_stop_pct = self.risk_manager.config.trailing_stop_pct

        result = await self.executor.place_order(request)

        order = Order(
            exchange=request.exchange,
            symbol=request.symbol,
            side=request.side.value,
            order_type=request.order_type.value,
            status=result["status"],
            quantity=request.quantity,
            price=request.price,
            filled_quantity=result.get("filled_quantity", Decimal("0")),
            average_price=result.get("average_price"),
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            trailing_stop_pct=request.trailing_stop_pct,
            external_id=result.get("external_id"),
            trading_mode=result.get("trading_mode", TradingMode.PAPER.value),
        )
        session.add(order)
        await session.flush()

        if result["status"] == OrderStatus.FILLED.value:
            position = Position(
                exchange=request.exchange,
                symbol=request.symbol,
                side=request.side.value,
                quantity=result["filled_quantity"],
                entry_price=result["average_price"] or request.price or Decimal("0"),
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
                trailing_stop_pct=request.trailing_stop_pct,
                trading_mode=order.trading_mode,
            )
            session.add(position)
            self.risk_manager.total_exposure += exposure
            self.risk_manager.orders_this_hour += 1

        await AuditService.log_order(
            session,
            order.id,
            "order_executed",
            {"symbol": request.symbol, "side": request.side.value, "status": result["status"]},
        )

        logger.info("order_executed", order_id=str(order.id), symbol=request.symbol)
        return order

    async def cancel_order(self, session: AsyncSession, order: Order) -> Order:
        if order.external_id:
            await self.executor.cancel_order(order.external_id, order.symbol)
        order.status = OrderStatus.CANCELLED.value
        await AuditService.log_order(session, order.id, "order_cancelled", {"symbol": order.symbol})
        return order
