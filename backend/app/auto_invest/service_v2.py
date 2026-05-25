"""Auto Invest V2 — análise completa + filtros de qualidade."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.consensus_v3.engine import ConsensusEngineV3
from backend.app.ai.regime.service import RegimeDetectionService
from backend.app.auto_invest.signal_freshness import SignalFreshnessValidator
from backend.app.data.collectors.binance_collector import BinanceCollector
from backend.app.features.service import FeatureStoreService
from backend.app.learning.trade_memory.service import TradeMemoryService
from backend.app.risk.engine_v2 import RiskEngineV2
from backend.app.risk.position_sizing import PositionSizingService
from backend.investment.advisor import build_investment_recommendation
from backend.investment.auto_invest import execute_proposed_order
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.paper_trial.service import get_trial_status, run_learning_cycle, start_trial
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models import OrderStatus

logger = get_logger("cryptoghost.v6.auto_invest")


class AutoInvestV2Service:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.orchestrator = IntelligenceOrchestrator()
        self.consensus_v3 = ConsensusEngineV3()
        self.regime_svc = RegimeDetectionService()
        self.features = FeatureStoreService()
        self.freshness = SignalFreshnessValidator()
        self.risk = RiskEngineV2()
        self.sizing = PositionSizingService()
        self.trade_memory = TradeMemoryService()
        self.collector = BinanceCollector()

    async def run_full_analysis(self, session: AsyncSession, symbol: str) -> dict:
        """Pipeline completo v2→v6 para um símbolo."""
        await self.features.get_or_compute(session, symbol)
        regime, policy, _ = await self.regime_svc.detect_and_persist(session, symbol)
        result = await self.orchestrator.analyze_symbol(session, symbol)

        consensus_data = result.get("consensus_v3") or result.get("consensus", {})
        if isinstance(consensus_data, dict) and "final_score" not in consensus_data:
            from backend.ai_consensus_engine.consensus import AgentVote

            votes = []
            for v in consensus_data.get("agent_votes", []):
                if isinstance(v, dict):
                    votes.append(AgentVote(
                        v.get("agent", "?"), v.get("decision", "HOLD"),
                        v.get("confidence", 0.5), v.get("raw_signal", ""), v.get("weight", 0.2),
                    ))
            weights = await self.consensus_v3.performance.compute_weights(
                session, symbol, regime.value
            )
            c3 = self.consensus_v3.build_from_votes(
                symbol, votes,
                calibrated_confidence=result.get("quant_v3", {}).get("calibration", {}).get("calibrated_confidence", 0.5),
                technical_score=float(result.get("analysis", {}).get("score", 50)),
                sentiment_score=float(result.get("sentiment", {}).get("score", 0)),
                regime=regime,
                policy=policy,
                agent_weights=weights,
            )
            result["consensus_v3"] = ConsensusEngineV3.to_dict(c3)
            await self.freshness.persist_signal(session, c3, regime.value)

        return result

    async def run_autonomous_cycle(self, session: AsyncSession, actor: str = "ai_autonomous_v2") -> dict:
        if not self.settings.auto_invest_enabled:
            return {"status": "disabled"}

        await start_trial(session, actor=actor)

        best_symbol = None
        best_score = 0.0
        best_c3 = None

        for symbol in self.settings.investment_universe_list:
            try:
                analysis = await self.run_full_analysis(session, symbol)
                c3_data = analysis.get("consensus_v3", {})
                score = float(c3_data.get("final_score", 0))
                if score > best_score:
                    best_score = score
                    best_symbol = symbol
                    best_c3 = c3_data
            except Exception as exc:
                logger.warning("analysis_failed", symbol=symbol, error=str(exc))

        recommendation = await build_investment_recommendation(session)
        order = None
        order_status = "skipped"

        if best_c3 and best_c3.get("can_execute") and best_symbol:
            rec_symbol = recommendation.get("best_symbol", best_symbol)
            if rec_symbol != best_symbol:
                recommendation = await build_investment_recommendation(session)

            proposed = recommendation.get("proposed_order") or {}
            if proposed.get("can_execute") and float(best_c3.get("final_score", 0)) >= self.settings.min_final_score_buy:
                price = Decimal(str(proposed.get("price", 0)))
                portfolio = Decimal(str(self.settings.paper_portfolio_usdt))
                qty, alloc_pct = self.sizing.compute_quantity(
                    float(best_c3["final_score"]), price, portfolio
                )
                if qty > 0:
                    can, reason = await self.risk.can_open(
                        session, qty * price, float(best_c3["final_score"])
                    )
                    if can:
                        proposed["quantity"] = str(qty)
                        proposed["allocation_pct"] = alloc_pct
                        proposed["final_score"] = best_c3.get("final_score")
                        order = await execute_proposed_order(session, proposed, actor, auto=True)
                        if order and order.status == OrderStatus.FILLED.value:
                            order_status = "executed"
                            await self.trade_memory.record_open(
                                session, order, best_c3, regime=best_c3.get("regime", "unknown")
                            )
                        elif order:
                            order_status = order.status
                    else:
                        order_status = f"rejected: {reason}"
                else:
                    order_status = "size_zero"
            else:
                order_status = "signal_weak"
        elif best_c3:
            order_status = "consensus_blocked"

        learning = await run_learning_cycle(session, actor=actor)
        trial = await get_trial_status(session)

        return {
            "status": "ok",
            "version": "v2",
            "best_symbol": best_symbol,
            "best_score": best_score,
            "consensus_v3": best_c3,
            "recommendation": {
                "symbol": recommendation.get("best_symbol"),
                "recommendation": recommendation.get("recommendation"),
            },
            "order": {
                "executed": order is not None and order.status == OrderStatus.FILLED.value,
                "status": order_status,
                "symbol": best_symbol,
            },
            "learning": {
                "validated": learning.get("validated_predictions", 0),
                "memory_updated": learning.get("memory_updated", 0),
            },
            "trial": trial,
        }
