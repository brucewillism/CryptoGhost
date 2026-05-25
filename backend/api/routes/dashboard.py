"""CryptoGhost - Rotas de dashboard e monitoramento."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import AuditLogResponse, DashboardStats, RiskStatusResponse
from backend.app.data.cache.data_cache import DataCache
from backend.data_collector.collector import ExchangeConnector
from backend.paper_trial.service import _portfolio_metrics
from backend.risk_management.manager import RiskManager
from backend.shared.config import get_settings
from backend.shared.database import get_async_session
from backend.shared.models import AIPrediction, AuditLog, Order, Position
from backend.shared.models_intelligence import AIConsensusRecord
from backend.shared.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
_ticker_cache = DataCache(namespace="dashboard_ticker", default_ttl=30)


def _fetch_ticker_cached(connector: ExchangeConnector, symbol: str) -> dict:
    key = f"ticker:{symbol}"
    cached = _ticker_cache.get(key)
    if cached:
        return cached
    ticker = connector.fetch_ticker(symbol)
    _ticker_cache.set(key, ticker, ttl=30)
    return ticker


async def _refresh_positions_pnl(session: AsyncSession) -> tuple[Decimal, Decimal]:
    """Atualiza P&L das posições abertas com preço real de mercado."""
    result = await session.execute(select(Position).where(Position.is_open == True))  # noqa: E712
    positions = result.scalars().all()
    if not positions:
        return Decimal("0"), Decimal("0")

    connector = ExchangeConnector("binance")
    total_unrealized = Decimal("0")
    total_exposure = Decimal("0")

    for pos in positions:
        try:
            ticker = _fetch_ticker_cached(connector, pos.symbol)
            current = Decimal(str(ticker.get("last") or ticker.get("close") or pos.entry_price))
        except Exception:
            current = pos.current_price or pos.entry_price

        pos.current_price = current
        if pos.side == "buy":
            pos.unrealized_pnl = (current - pos.entry_price) * pos.quantity
        else:
            pos.unrealized_pnl = (pos.entry_price - current) * pos.quantity
        total_unrealized += pos.unrealized_pnl
        total_exposure += current * pos.quantity

    return total_unrealized, total_exposure


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> DashboardStats:
    settings = get_settings()
    risk_manager = RiskManager()

    open_positions = await session.scalar(
        select(func.count()).select_from(Position).where(Position.is_open == True)  # noqa: E712
    )
    total_orders = await session.scalar(select(func.count()).select_from(Order))

    unrealized_pnl, exposure = await _refresh_positions_pnl(session)
    portfolio = await _portfolio_metrics(session)

    latest_consensus = await session.execute(
        select(AIConsensusRecord).order_by(AIConsensusRecord.created_at.desc()).limit(1)
    )
    consensus = latest_consensus.scalar_one_or_none()

    if consensus:
        ai_signal = consensus.final_decision.lower()
        ai_confidence = consensus.confidence
    else:
        latest_prediction = await session.execute(
            select(AIPrediction).order_by(AIPrediction.created_at.desc()).limit(1)
        )
        prediction = latest_prediction.scalar_one_or_none()
        ai_signal = prediction.signal if prediction else "hold"
        ai_confidence = prediction.confidence if prediction else 0.0

    return DashboardStats(
        total_pnl=float(unrealized_pnl),
        paper_portfolio_value=portfolio["current_value_usdt"],
        paper_return_pct=portfolio["return_pct"],
        open_positions=open_positions or 0,
        total_orders=total_orders or 0,
        ai_signal=ai_signal,
        ai_confidence=ai_confidence,
        risk_status=RiskStatusResponse(
            daily_pnl=float(unrealized_pnl),
            max_daily_loss=float(risk_manager.max_daily_loss),
            total_exposure=float(exposure or risk_manager.total_exposure),
            max_exposure=float(risk_manager.max_exposure),
            trading_halted=risk_manager.trading_halted,
            circuit_breaker_active=risk_manager.circuit_breaker_active,
            paper_trading=settings.paper_trading,
            live_trading_enabled=settings.live_trading_enabled,
        ),
        auto_invest_interval_minutes=settings.auto_invest_interval_minutes,
    )


@router.get("/live")
async def get_live_dashboard(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    from backend.api.services.live_dashboard import build_live_snapshot

    return await build_live_snapshot(session)


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    event_type: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> list[AuditLog]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    result = await session.execute(query)
    return list(result.scalars().all())
