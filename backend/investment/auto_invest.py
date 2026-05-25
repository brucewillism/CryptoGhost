"""CryptoGhost - Execução autônoma de investimentos paper."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_collector.collector import ExchangeConnector
from backend.investment.advisor import build_investment_recommendation
from backend.paper_trial.service import get_trial_status, run_learning_cycle, start_trial
from backend.shared.config import get_settings
from backend.shared.models import AuditEventType, Order, OrderStatus
from backend.audit_logs.service import AuditService
from backend.trading_engine.engine import OrderRequest, TradingEngine
from backend.shared.models import OrderSide, OrderType


async def execute_proposed_order(
    session: AsyncSession,
    proposed: dict,
    actor: str,
    *,
    auto: bool = False,
) -> Order | None:
    if not proposed.get("can_execute") or proposed.get("side") != "buy":
        return None

    connector = ExchangeConnector("binance")
    ticker = connector.fetch_ticker(proposed["symbol"])
    market_price = Decimal(str(ticker.get("last") or ticker.get("close")))

    engine = TradingEngine()
    order_request = OrderRequest(
        exchange="binance",
        symbol=proposed["symbol"],
        side=OrderSide.BUY,
        quantity=Decimal(proposed["quantity"]),
        order_type=OrderType.MARKET,
        price=market_price,
        stop_loss=Decimal(proposed["stop_loss"]) if proposed.get("stop_loss") else None,
        take_profit=Decimal(proposed["take_profit"]) if proposed.get("take_profit") else None,
        metadata={"final_score": proposed.get("final_score", proposed.get("score", 60))},
    )
    order = await engine.execute_order(session, order_request, actor=actor)

    await AuditService.log(
        session,
        AuditEventType.FINANCIAL,
        "auto_investment" if auto else "investment_approved",
        actor=actor,
        details={
            "symbol": proposed["symbol"],
            "quantity": proposed["quantity"],
            "price": str(market_price),
            "auto": auto,
            "status": order.status,
        },
    )
    return order


async def run_autonomous_cycle(session: AsyncSession, actor: str = "ai_autonomous") -> dict:
    """Analisa oportunidade, investe paper automaticamente e roda aprendizado."""
    settings = get_settings()
    if not settings.auto_invest_enabled:
        return {"status": "disabled", "message": "Investimento autônomo desativado no .env"}

    if settings.v6_enabled and settings.auto_invest_v2_enabled:
        from backend.app.auto_invest.service_v2 import AutoInvestV2Service
        return await AutoInvestV2Service().run_autonomous_cycle(session, actor=actor)

    await start_trial(session, actor=actor)
    recommendation = await build_investment_recommendation(session)

    order = None
    order_status = "skipped"
    proposed = recommendation.get("proposed_order") or {}

    if recommendation.get("status") == "ready" and proposed.get("can_execute"):
        order = await execute_proposed_order(session, proposed, actor, auto=True)
        if order:
            order_status = order.status
            if order.status == OrderStatus.REJECTED.value:
                order_status = "rejected"

    learning = await run_learning_cycle(session, actor=actor)
    trial = await get_trial_status(session)

    return {
        "status": "ok",
        "auto_invest": True,
        "recommendation": {
            "symbol": recommendation.get("best_symbol"),
            "recommendation": recommendation.get("recommendation"),
            "expected_return_pct": recommendation.get("expected_return_pct"),
            "ai_summary": recommendation.get("ai_summary"),
        },
        "order": {
            "executed": order is not None and order.status == OrderStatus.FILLED.value,
            "status": order_status,
            "symbol": proposed.get("symbol"),
            "quantity": proposed.get("quantity"),
        } if proposed else {"executed": False, "status": "no_opportunity"},
        "learning": {
            "validated": learning.get("validated_predictions", 0),
            "memory_updated": learning.get("memory_updated", 0),
        },
        "trial": trial,
    }
