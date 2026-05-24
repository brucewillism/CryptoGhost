"""CryptoGhost v5 - Self-Improving Pipeline."""

import time
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adaptive_weighting.engine import AdaptiveWeightingEngine
from backend.ai_truth_engine.engine import AITruthEngine
from backend.drift_detection.engine import DriftDetectionEngine
from backend.institutional_data_lake.lake import InstitutionalDataLake
from backend.institutional_data_lake.premium_connectors import PremiumDataHub
from backend.institutional_backtesting.engine import InstitutionalBacktestingEngine
from backend.market_state_intelligence.engine import MarketStateIntelligence
from backend.meta_learning_engine.engine import MetaLearningEngine
from backend.orderflow_ai.engine import OrderflowAI
from backend.portfolio_survival.engine import PortfolioSurvivalEngine
from backend.prediction_validation.engine import PredictionValidationEngine
from backend.real_performance_tracker.engine import RealPerformanceTracker
from backend.self_improvement_engine.engine import SelfImprovementEngine
from backend.self_improving.context import SelfImprovingContext
from backend.strategy_evolution.engine import StrategyEvolutionEngine
from backend.timing_optimization.engine import TimingOptimizationEngine
from backend.event_bus.bus import EventType, get_event_bus
from backend.shared.logging_config import get_logger
from backend.shared.metrics import (
    AI_TRUTH_SCORE,
    DRIFT_V5_SCORE,
    PREDICTION_ACCURACY,
    SURVIVAL_SCORE_GAUGE,
    SELF_IMPROVEMENT_COUNTER,
)
from backend.shared.models_v5 import (
    AITruthRecord,
    DriftDetectionRecord,
    MarketStateRecord,
    MetaLearningRecord,
    OrderflowSnapshotRecord,
    PredictionValidationRecord,
    RealPerformanceRecord,
    SelfImprovementRecord,
    StrategyEvolutionRecord,
)

logger = get_logger("cryptoghost.self_improving.pipeline")


class SelfImprovingPipeline:
    """Orquestra plataforma quantitativa auto-evolutiva v5."""

    def __init__(self) -> None:
        self.meta = MetaLearningEngine()
        self.self_improve = SelfImprovementEngine()
        self.data_lake = InstitutionalDataLake()
        self.premium = PremiumDataHub()
        self.orderflow = OrderflowAI()
        self.timing = TimingOptimizationEngine()
        self.survival = PortfolioSurvivalEngine()
        self.validation = PredictionValidationEngine()
        self.strategy_evo = StrategyEvolutionEngine()
        self.drift = DriftDetectionEngine()
        self.performance = RealPerformanceTracker()
        self.truth = AITruthEngine()
        self.weighting = AdaptiveWeightingEngine()
        self.backtest = InstitutionalBacktestingEngine()
        self.market_state = MarketStateIntelligence()
        self.event_bus = get_event_bus()

    async def enhance(
        self,
        session: AsyncSession,
        ctx: SelfImprovingContext,
    ) -> dict:
        start = time.perf_counter()

        premium_data = await self.premium.aggregate(ctx.symbol)
        ctx.premium_data = premium_data

        orderbook = self.orderflow.fetch_orderbook(ctx.symbol)
        of = self.orderflow.analyze(ctx.df, ctx.symbol, orderbook)

        market_st = self.market_state.analyze(ctx.df, ctx.symbol, of.spoofing_detected)

        validation = self.validation.validate(
            ctx.symbol, ctx.expected_return, ctx.confidence, ctx.df,
        )

        meta_metrics = self.meta.build_metrics_from_forecast(ctx.investment_v4)
        meta_sel = self.meta.select_best_model(ctx.regime, meta_metrics)

        drift_reports = self.drift.detect(ctx.df, meta_sel.best_model, ctx.regime)
        max_drift = self.drift.max_drift_score(drift_reports)

        truth = self.truth.assess(
            ctx.symbol, ctx.confidence, validation.validation_score,
            validation.rolling_accuracy,
            {
                "has_forecast": bool(ctx.investment_v4),
                "has_orderflow": True,
                "has_premium_data": bool(premium_data),
                "conflicting_signals": of.smart_money_direction == "bearish" and ctx.decision == "BUY",
            },
        )

        timing = self.timing.optimize(ctx.df, ctx.symbol, ctx.decision, of.delta_imbalance)

        survival = self.survival.assess(
            ctx.crash_probability, ctx.volatility, 0,
            systemic_risk=market_st.hidden_risk_score,
        )

        weights = self.weighting.compute(
            ctx.regime, drawdown_pct=0, volatility=ctx.volatility,
            self_improvement_weights=self.self_improve.current_weights,
        )

        improvements = self.self_improve.process_feedback(
            validation.validation_score, validation.direction_correct,
            validation.false_positive, max_drift > 0.2,
        )

        evolved = self.strategy_evo.evolve(ctx.df, generations=2)
        bt = self.backtest.run(ctx.df, ctx.symbol)
        perf = self.performance.compute(bt.equity_curve)

        self.data_lake.ingest_analysis_bundle(
            ctx.symbol, ctx.v2_result, ctx.quant_v3, ctx.investment_v4,
        )
        self.data_lake.ingest("orderflow", asdict(of), ctx.symbol)

        await self._persist(
            session, ctx, meta_sel, validation, truth, drift_reports,
            market_st, of, evolved, perf, improvements,
        )

        AI_TRUTH_SCORE.labels(symbol=ctx.symbol).set(truth.truth_score)
        DRIFT_V5_SCORE.labels(model=meta_sel.best_model).set(max_drift)
        PREDICTION_ACCURACY.labels(symbol=ctx.symbol).set(validation.rolling_accuracy)
        SURVIVAL_SCORE_GAUGE.set(survival.survival_score)
        SELF_IMPROVEMENT_COUNTER.inc(len(improvements))

        self.event_bus.publish_sync(EventType.DRIFT, {
            "symbol": ctx.symbol, "drift_score": max_drift, "retrain": max_drift > 0.2,
        })

        elapsed = (time.perf_counter() - start) * 1000

        corrected_confidence = truth.corrected_confidence * meta_sel.confidence_correction

        return {
            "meta_learning": {
                "best_model": meta_sel.best_model,
                "market_regime": meta_sel.market_regime,
                "historical_accuracy": meta_sel.historical_accuracy,
                "model_weights": meta_sel.model_weights,
            },
            "ai_truth": {
                "truth_score": truth.truth_score,
                "raw_confidence": truth.raw_confidence,
                "corrected_confidence": round(corrected_confidence, 4),
                "overconfidence_detected": truth.overconfidence_detected,
                "honest": truth.honest,
            },
            "prediction_validation": asdict(validation),
            "drift_detection": [asdict(d) for d in drift_reports],
            "orderflow": {
                "cumulative_delta": of.cumulative_delta,
                "delta_imbalance": of.delta_imbalance,
                "smart_money_direction": of.smart_money_direction,
                "absorption": of.absorption_detected,
                "spoofing": of.spoofing_detected,
            },
            "timing": asdict(timing),
            "survival": asdict(survival),
            "market_state": asdict(market_st),
            "adaptive_weights": asdict(weights),
            "self_improvement": [asdict(i) for i in improvements],
            "strategy_evolution": asdict(evolved),
            "real_performance": asdict(perf),
            "institutional_backtest": {
                "return_pct": bt.total_return_pct,
                "sharpe": bt.sharpe_ratio,
                "max_drawdown_pct": bt.max_drawdown_pct,
                "avg_slippage_pct": bt.avg_slippage_pct,
            },
            "premium_data": premium_data,
            "v5_elapsed_ms": round(elapsed, 1),
        }

    async def _persist(self, session, ctx, meta, validation, truth, drifts, market_st, of, evolved, perf, improvements):
        session.add(MetaLearningRecord(
            model_name=meta.best_model, market_regime=meta.market_regime,
            historical_accuracy=meta.historical_accuracy, sharpe_ratio=meta.sharpe_ratio,
            weight=meta.model_weights.get(meta.best_model, 1), is_best=True,
            metadata_=meta.model_weights,
        ))
        session.add(PredictionValidationRecord(
            symbol=ctx.symbol, predicted_return_pct=validation.predicted_return_pct,
            actual_return_pct=validation.actual_return_pct,
            predicted_confidence=validation.predicted_confidence,
            calibration_error=validation.calibration_error,
            direction_correct=validation.direction_correct,
            validation_score=validation.validation_score,
        ))
        session.add(AITruthRecord(
            symbol=ctx.symbol, truth_score=truth.truth_score,
            raw_confidence=truth.raw_confidence, corrected_confidence=truth.corrected_confidence,
            overconfidence_detected=truth.overconfidence_detected,
            hallucination_risk=truth.hallucination_risk, validation_basis=truth.validation_basis,
        ))
        for d in drifts:
            session.add(DriftDetectionRecord(
                model_name=d.model_name, drift_type=d.drift_type, drift_score=d.drift_score,
                regime_shift_detected=d.regime_shift_detected, retrain_triggered=d.retrain_triggered,
                details=d.details,
            ))
        session.add(MarketStateRecord(
            symbol=ctx.symbol, structural_state=market_st.structural_state,
            fragility_score=market_st.fragility_score, hidden_risk_score=market_st.hidden_risk_score,
            trend_exhaustion=market_st.trend_exhaustion, manipulation_score=market_st.manipulation_score,
            details=market_st.details,
        ))
        session.add(OrderflowSnapshotRecord(
            symbol=ctx.symbol, cumulative_delta=of.cumulative_delta,
            delta_imbalance=of.delta_imbalance, absorption_detected=of.absorption_detected,
            spoofing_detected=of.spoofing_detected, smart_money_direction=of.smart_money_direction,
            footprint=of.footprint,
        ))
        session.add(StrategyEvolutionRecord(
            strategy_id=evolved.strategy_id, generation=evolved.generation,
            fitness_score=evolved.fitness_score, parameters=evolved.parameters,
            sharpe_ratio=evolved.sharpe_ratio, max_drawdown_pct=evolved.max_drawdown_pct,
            promoted=evolved.fitness_score > 10,
        ))
        session.add(RealPerformanceRecord(
            sharpe_ratio=perf.sharpe_ratio, sortino_ratio=perf.sortino_ratio,
            max_drawdown_pct=perf.max_drawdown_pct, cagr_pct=perf.cagr_pct,
            hit_rate=perf.hit_rate, expected_vs_actual_pct=perf.expected_vs_actual_pct,
            alpha_pct=perf.alpha_pct, metrics={"total_return": perf.total_return_pct},
        ))
        for imp in improvements:
            session.add(SelfImprovementRecord(
                action_type=imp.action_type, target=imp.target,
                before_value=imp.before_value, after_value=imp.after_value,
                improvement_pct=imp.improvement_pct, details=imp.details,
            ))

    @staticmethod
    def build_context(symbol: str, df, v2_result: dict, quant_v3=None, investment_v4=None) -> SelfImprovingContext:
        regime = str(v2_result.get("regime", {}).get("regime", "sideways"))
        return SelfImprovingContext(
            symbol=symbol, df=df, regime=regime,
            v2_result=v2_result, quant_v3=quant_v3, investment_v4=investment_v4,
        )
