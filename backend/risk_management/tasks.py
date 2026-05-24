"""CryptoGhost - Celery tasks de monitoramento de risco."""

from backend.shared.celery_app import celery_app
from backend.shared.database import SyncSessionLocal
from backend.shared.logging_config import get_logger
from backend.shared.models import Position, RiskState
from backend.risk_management.manager import RiskManager

logger = get_logger("cryptoghost.risk_management.tasks")


@celery_app.task(name="backend.risk_management.tasks.monitor_risk")
def monitor_risk() -> dict:
    """Monitora posições abertas e aplica regras de risco."""
    manager = RiskManager()
    actions = []

    with SyncSessionLocal() as session:
        risk_state = session.query(RiskState).first()
        if not risk_state:
            risk_state = RiskState(id=1)
            session.add(risk_state)

        positions = session.query(Position).filter(Position.is_open == True).all()  # noqa: E712

        for pos in positions:
            if not pos.current_price:
                continue

            position_risk = __import__(
                "backend.risk_management.manager", fromlist=["PositionRisk"]
            ).PositionRisk(
                symbol=pos.symbol,
                entry_price=pos.entry_price,
                quantity=pos.quantity,
                side=pos.side,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                trailing_stop_pct=pos.trailing_stop_pct,
            )

            trigger = manager.check_stop_conditions(position_risk, pos.current_price)
            if trigger:
                actions.append({"symbol": pos.symbol, "action": trigger, "position_id": str(pos.id)})
                logger.warning("risk_trigger", symbol=pos.symbol, trigger=trigger)

        risk_state.daily_pnl = manager.daily_pnl
        risk_state.total_exposure = manager.total_exposure
        risk_state.trading_halted = manager.trading_halted
        risk_state.circuit_breaker_active = manager.circuit_breaker_active
        session.commit()

    return {"status": "ok", "actions": actions, "risk_status": manager.get_status()}
