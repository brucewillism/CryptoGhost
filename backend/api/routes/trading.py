"""CryptoGhost - Rotas de trading."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import ApprovedInvestmentRequest, OrderCreateRequest, OrderResponse, PositionResponse
from backend.audit_logs.service import AuditService
from backend.shared.database import get_async_session
from backend.shared.models import Order, OrderSide, OrderStatus, OrderType, Position
from backend.shared.security import UserRole, get_current_user, require_role
from backend.trading_engine.engine import OrderRequest, TradingEngine

router = APIRouter(prefix="/trading", tags=["Trading"])


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: OrderCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR)),
) -> Order:
    engine = TradingEngine()
    order_request = OrderRequest(
        exchange=request.exchange,
        symbol=request.symbol,
        side=OrderSide(request.side),
        quantity=request.quantity,
        order_type=OrderType(request.order_type),
        price=request.price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )
    order = await engine.execute_order(session, order_request, actor=user["username"])
    return order


@router.post("/approve-investment", response_model=OrderResponse)
async def approve_investment(
    request: ApprovedInvestmentRequest,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
) -> Order:
    """Executa investimento paper/live após confirmação explícita do usuário."""
    if not request.user_confirmed:
        raise HTTPException(status_code=400, detail="Confirmação do usuário é obrigatória")

    from backend.data_collector.collector import ExchangeConnector

    connector = ExchangeConnector("binance")
    ticker = connector.fetch_ticker(request.symbol)
    market_price = Decimal(str(ticker.get("last") or ticker.get("close")))

    engine = TradingEngine()
    order_request = OrderRequest(
        exchange="binance",
        symbol=request.symbol,
        side=OrderSide(request.side),
        quantity=request.quantity,
        order_type=OrderType.MARKET,
        price=market_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )
    order = await engine.execute_order(session, order_request, actor=user["username"])
    await AuditService.log(
        session,
        AuditEventType.FINANCIAL,
        "investment_approved",
        actor=user["username"],
        details={
            "symbol": request.symbol,
            "side": request.side,
            "quantity": str(request.quantity),
            "price": str(market_price),
        },
    )
    if order.status == OrderStatus.REJECTED.value:
        raise HTTPException(status_code=400, detail=order.metadata_.get("rejection_reason", "Ordem rejeitada pelo risk manager"))
    return order


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> list[Order]:
    result = await session.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
    return list(result.scalars().all())


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> Order:
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    return order


@router.delete("/orders/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR)),
) -> Order:
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")
    engine = TradingEngine()
    return await engine.cancel_order(session, order)


@router.get("/positions", response_model=list[PositionResponse])
async def list_positions(
    open_only: bool = True,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> list[Position]:
    query = select(Position)
    if open_only:
        query = query.where(Position.is_open == True)  # noqa: E712
    result = await session.execute(query.order_by(Position.opened_at.desc()))
    return list(result.scalars().all())
