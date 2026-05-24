"""CryptoGhost - Rotas de risco e comparador."""

from fastapi import APIRouter, Depends

from backend.api.schemas import BrokerCompareRequest, RiskStatusResponse
from backend.broker_comparator.comparator import BrokerComparator
from backend.data_collector.collector import MarketDataCollector
from backend.risk_management.manager import RiskManager
from backend.shared.config import get_settings
from backend.shared.security import get_current_user

router = APIRouter(tags=["Risco & Corretoras"])


@router.get("/risk/status", response_model=RiskStatusResponse)
async def get_risk_status(_user: dict = Depends(get_current_user)) -> RiskStatusResponse:
    settings = get_settings()
    manager = RiskManager()
    status = manager.get_status()
    return RiskStatusResponse(
        daily_pnl=status["daily_pnl"],
        max_daily_loss=status["max_daily_loss"],
        total_exposure=status["total_exposure"],
        max_exposure=status["max_exposure"],
        trading_halted=status["trading_halted"],
        circuit_breaker_active=status["circuit_breaker_active"],
        paper_trading=settings.paper_trading,
        live_trading_enabled=settings.live_trading_enabled,
    )


@router.post("/brokers/compare")
async def compare_brokers(
    request: BrokerCompareRequest,
    _user: dict = Depends(get_current_user),
) -> dict:
    collector = MarketDataCollector(exchanges=request.exchanges)
    snapshots = collector.collect_snapshot(request.symbol)
    metrics = BrokerComparator.from_market_snapshots(snapshots)
    comparator = BrokerComparator()
    ranking = comparator.compare(metrics)
    return {"symbol": request.symbol, "ranking": ranking, "selected": ranking[0] if ranking else None}
