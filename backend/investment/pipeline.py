"""CryptoGhost v4 - Investment Pipeline."""

import time
from dataclasses import asdict

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adaptive_portfolio_engine.engine import AdaptivePortfolioEngine
from backend.ai_forecast_engine.engine import AIForecastEngine
from backend.ai_router.router import get_ai_router
from backend.alpha_detection.engine import AlphaDetectionEngine
from backend.capital_allocator.engine import CapitalAllocator
from backend.institutional_signal_engine.engine import InstitutionalSignalEngine
from backend.investment.context import MarketContext
from backend.investment_prioritizer.engine import InvestmentPrioritizer
from backend.opportunity_scoring.engine import OpportunityScoringEngine
from backend.predictive_profit_engine.engine import PredictiveProfitEngine
from backend.probabilistic_analysis.engine import ProbabilisticAnalysisEngine
from backend.profit_probability_engine.engine import ProfitProbabilityEngine
from backend.risk_reward_optimizer.engine import RiskRewardOptimizer
from backend.smart_asset_ranking.engine import SmartAssetRankingEngine
from backend.smart_position_sizing.engine import SmartPositionSizingEngine
from backend.event_bus.bus import EventType, get_event_bus
from backend.shared.logging_config import get_logger
from backend.shared.metrics import (
    INVESTMENT_RANKING_SCORE,
    OPPORTUNITY_SCORE_GAUGE,
    PROFIT_PROBABILITY_GAUGE,
    EXPECTED_RETURN_GAUGE,
)
from backend.shared.models_investment import (
    AdaptiveAllocationRecord,
    AlphaDetectionRecord,
    ExpectedReturnRecord,
    InstitutionalSignalRecord,
    InvestmentRankingRecord,
    OpportunityScoreRecord,
    ProbabilisticPredictionRecord,
)

logger = get_logger("cryptoghost.investment.pipeline")


class InvestmentPipeline:
    """Orquestra priorização inteligente de investimentos."""

    def __init__(self) -> None:
        self.opportunity = OpportunityScoringEngine()
        self.profit_forecast = PredictiveProfitEngine()
        self.probabilistic = ProbabilisticAnalysisEngine()
        self.profit_prob = ProfitProbabilityEngine()
        self.risk_reward = RiskRewardOptimizer()
        self.alpha = AlphaDetectionEngine()
        self.institutional = InstitutionalSignalEngine()
        self.forecast = AIForecastEngine()
        self.position_sizing = SmartPositionSizingEngine()
        self.prioritizer = InvestmentPrioritizer()
        self.ranking = SmartAssetRankingEngine()
        self.allocator = CapitalAllocator()
        self.portfolio = AdaptivePortfolioEngine()
        self.ai_router = get_ai_router()
        self.event_bus = get_event_bus()

    async def analyze_symbol(
        self,
        session: AsyncSession,
        ctx: MarketContext,
        market_avg_score: float = 50.0,
    ) -> dict:
        start = time.perf_counter()

        inst = self.institutional.analyze(ctx)
        opportunity = self.opportunity.score(ctx, inst.overall_strength)
        forecast_profit = self.profit_forecast.forecast(ctx)
        prob = self.probabilistic.analyze(ctx)
        ai_fc = self.forecast.forecast(ctx)

        sim_bull = 0.5
        if ctx.quant_v3 and ctx.quant_v3.get("similarity"):
            sim_bull = ctx.quant_v3["similarity"].get("aggregate_probability", {}).get("bullish_prob", 0.5)

        profit_p = self.profit_prob.calculate(ctx, prob, forecast_profit, opportunity, sim_bull)
        rr = self.risk_reward.assess(ctx, forecast_profit, profit_p)
        alpha = self.alpha.detect(ctx, market_avg_score)
        priority = self.prioritizer.prioritize(
            ctx, opportunity.opportunity_score, forecast_profit.expected_return_pct,
            profit_p.profit_probability, rr.risk_reward_score, alpha.alpha_score,
            rr.approved, inst.overall_strength,
        )
        sizing = self.position_sizing.calculate(ctx, rr)

        await self._persist(session, ctx, opportunity, forecast_profit, prob, inst, alpha, priority)

        INVESTMENT_RANKING_SCORE.labels(symbol=ctx.symbol).set(priority.priority_score)
        OPPORTUNITY_SCORE_GAUGE.labels(symbol=ctx.symbol).set(opportunity.opportunity_score)
        PROFIT_PROBABILITY_GAUGE.labels(symbol=ctx.symbol).set(profit_p.profit_probability)
        EXPECTED_RETURN_GAUGE.labels(symbol=ctx.symbol).set(forecast_profit.expected_return_pct)

        self.event_bus.publish_sync(EventType.AI_DECISION, {
            "symbol": ctx.symbol, "priority_score": priority.priority_score,
            "recommendation": priority.recommendation,
        })

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "priority": asdict(priority),
            "opportunity": asdict(opportunity),
            "forecast": asdict(forecast_profit),
            "probabilistic": asdict(prob),
            "profit_probability": asdict(profit_p),
            "risk_reward": asdict(rr),
            "alpha": asdict(alpha),
            "institutional": {
                "net_flow_score": inst.net_flow_score,
                "accumulation": inst.accumulation_detected,
                "whale_activity": inst.whale_activity,
                "signals": [asdict(s) for s in inst.signals[:5]],
            },
            "ai_forecast": asdict(ai_fc),
            "position_sizing": asdict(sizing),
            "explainable": {
                "decision": f"{priority.recommendation} {ctx.symbol}",
                "expected_return": f"{priority.expected_return}%",
                "risk": priority.risk_level,
                "confidence": priority.confidence,
                "reasons": priority.reasons,
            },
            "investment_elapsed_ms": round(elapsed, 1),
        }

    async def rank_universe(
        self,
        session: AsyncSession,
        contexts: list[MarketContext],
    ) -> dict:
        results = []
        avg_score = np.mean([c.score for c in contexts]) if contexts else 50

        for ctx in contexts:
            r = await self.analyze_symbol(session, ctx, avg_score)
            p = r["priority"]
            results.append({
                "symbol": ctx.symbol,
                "priority_score": p["priority_score"],
                "opportunity_score": r["opportunity"]["opportunity_score"],
                "profit_probability": p["profit_probability"],
                "risk_reward_score": r["risk_reward"]["risk_reward_score"],
                "alpha_score": r["alpha"]["alpha_score"],
                "confidence": p["confidence"],
                "expected_return": p["expected_return"],
                "risk_score": p["risk_score"],
                "recommendation": p["recommendation"],
                "approved": p["approved"],
                "liquidity_score": ctx.liquidity_score,
                "full": r,
            })

        ranked = self.ranking.rank(results)
        regime = contexts[0].regime_name if contexts else "sideways"
        vol = contexts[0].volatility if contexts else 50
        crash = contexts[0].crash_probability if contexts else 0

        allocation = self.allocator.allocate(results, regime)
        adaptation = self.portfolio.adapt(allocation, regime, vol, crash)

        for i, asset in enumerate(ranked):
            session.add(InvestmentRankingRecord(
                symbol=asset.symbol, asset_class="crypto",
                priority_score=asset.composite_score, rank_position=asset.rank,
                expected_return_pct=asset.expected_return_pct, risk_score=asset.risk_score,
                confidence=asset.confidence, recommendation=asset.recommendation,
                reasons=next((r["full"]["priority"]["reasons"] for r in results if r["symbol"] == asset.symbol), []),
            ))

        session.add(AdaptiveAllocationRecord(
            allocations=adaptation.adjusted_allocations,
            total_exposure_pct=100 - adaptation.adjusted_allocations.get("Cash", 0),
            cash_pct=adaptation.adjusted_allocations.get("Cash", 0),
            regime=regime, rationale="; ".join(adaptation.actions) or allocation.rationale,
        ))

        best = ranked[0] if ranked else None
        explanation = ""
        if best:
            best_data = next(r for r in results if r["symbol"] == best.symbol)
            explanation = await self.ai_router.explain_investment(best_data["full"]["explainable"])

        return {
            "best_opportunity": asdict(best) if best else None,
            "ranking": [asdict(a) for a in ranked],
            "allocation": asdict(allocation),
            "portfolio_adaptation": asdict(adaptation),
            "premium_explanation": explanation,
            "total_analyzed": len(contexts),
        }

    async def _persist(self, session, ctx, opportunity, forecast, prob, inst, alpha, priority) -> None:
        session.add(OpportunityScoreRecord(
            symbol=ctx.symbol, opportunity_score=opportunity.opportunity_score,
            classification=opportunity.classification, components=opportunity.components,
        ))
        session.add(ExpectedReturnRecord(
            symbol=ctx.symbol, expected_return_pct=forecast.expected_return_pct,
            drawdown_probable_pct=forecast.drawdown_probable_pct,
            upside_downside_ratio=forecast.upside_downside_ratio,
            horizon_days=forecast.horizon_days, confidence_interval=forecast.confidence_interval,
            method=forecast.method,
        ))
        session.add(ProbabilisticPredictionRecord(
            symbol=ctx.symbol, bullish_probability=prob.bullish_probability,
            bearish_probability=prob.bearish_probability, sideways_probability=prob.sideways_probability,
            uncertainty=prob.uncertainty, method=prob.method,
        ))
        session.add(AlphaDetectionRecord(
            symbol=ctx.symbol, alpha_score=alpha.alpha_score, alpha_type=alpha.alpha_type,
            expected_edge_pct=alpha.expected_edge_pct, rarity=alpha.rarity, details=alpha.details,
        ))
        for sig in inst.signals[:3]:
            session.add(InstitutionalSignalRecord(
                symbol=ctx.symbol, signal_type=sig.signal_type, strength=sig.strength,
                direction=sig.direction, source=sig.source, details=sig.details,
            ))

    @staticmethod
    def build_context(
        symbol: str,
        df: pd.DataFrame,
        v2_result: dict,
        quant_v3: dict | None = None,
        macro: dict | None = None,
        liquidity_score: float = 0.5,
        correlations: dict[str, float] | None = None,
    ) -> MarketContext:
        calibrated = 0.5
        if quant_v3 and quant_v3.get("calibration"):
            calibrated = quant_v3["calibration"].get("calibrated_confidence", 0.5)

        return MarketContext(
            symbol=symbol, df=df,
            analysis=v2_result.get("analysis", {}),
            sentiment=v2_result.get("sentiment", {}),
            risk=v2_result.get("risk", {}),
            regime=v2_result.get("regime", {}),
            consensus=v2_result.get("consensus", {}),
            explanation=v2_result.get("explanation", {}),
            macro=macro, quant_v3=quant_v3,
            calibrated_confidence=calibrated,
            liquidity_score=liquidity_score,
            correlations=correlations or {},
        )
