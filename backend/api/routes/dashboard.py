"""CryptoGhost - Rotas de dashboard e monitoramento."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import AuditLogResponse, DashboardStats, RiskStatusResponse
from backend.risk_management.manager import RiskManager
from backend.shared.config import get_settings
from backend.shared.database import get_async_session
from backend.shared.models import AIPrediction, AuditLog, Order, Position
from backend.shared.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


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

    latest_prediction = await session.execute(
        select(AIPrediction).order_by(AIPrediction.created_at.desc()).limit(1)
    )
    prediction = latest_prediction.scalar_one_or_none()

    return DashboardStats(
        open_positions=open_positions or 0,
        total_orders=total_orders or 0,
        ai_signal=prediction.signal if prediction else "hold",
        ai_confidence=prediction.confidence if prediction else 0.0,
        risk_status=RiskStatusResponse(
            daily_pnl=float(risk_manager.daily_pnl),
            max_daily_loss=float(risk_manager.max_daily_loss),
            total_exposure=float(risk_manager.total_exposure),
            max_exposure=float(risk_manager.max_exposure),
            trading_halted=risk_manager.trading_halted,
            circuit_breaker_active=risk_manager.circuit_breaker_active,
            paper_trading=settings.paper_trading,
            live_trading_enabled=settings.live_trading_enabled,
        ),
    )


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
