"""CryptoGhost v3 - Quant Pipeline (orquestração institucional)."""

import asyncio
import time
import uuid
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from backend.adaptive_strategy.engine import AdaptiveStrategyEngine
from backend.ai_calibration.calibrator import ConfidenceCalibrator
from backend.ai_performance_lab.lab import AIPerformanceLab
from backend.ensemble_engine.engine import AgentPrediction, EnsembleEngine
from backend.event_bus.bus import EventType, get_event_bus
from backend.feature_store.store import get_feature_store
from backend.gpu_inference.engine import get_gpu_engine
from backend.scenario_similarity.engine import ScenarioSimilarityEngine
from backend.shared.logging_config import get_logger
from backend.shared.models_quant import (
    CalibratedPredictionRecord,
    EnsembleDecisionRecord,
    ScenarioEmbeddingRecord,
)
from backend.temporal_memory.system import MemoryContext, TemporalMemorySystem

logger = get_logger("cryptoghost.quant.pipeline")


class QuantPipeline:
    """Pipeline v3: feature store → calibration → ensemble → similarity → adaptive."""

    def __init__(self) -> None:
        self.feature_store = get_feature_store()
        self.calibrator = ConfidenceCalibrator()
        self.ensemble = EnsembleEngine()
        self.similarity = ScenarioSimilarityEngine()
        self.adaptive = AdaptiveStrategyEngine()
        self.temporal = TemporalMemorySystem()
        self.performance_lab = AIPerformanceLab()
        self.event_bus = get_event_bus()
        self.gpu = get_gpu_engine()

    async def enhance_analysis(
        self,
        session: AsyncSession,
        symbol: str,
        v2_result: dict,
        df,
        regime: str,
        agreement_ratio: float,
    ) -> dict:
        start = time.perf_counter()

        analysis = v2_result.get("analysis", {})
        consensus = v2_result.get("consensus", {})
        risk = v2_result.get("risk", {})
        sentiment = v2_result.get("sentiment", {})

        self.feature_store.ingest_technical_features(session, symbol, analysis.get("indicators", {}))
        self.feature_store.ingest_sentiment_features(session, sentiment)

        raw_conf = consensus.get("confidence", 0.5)
        calibrated = self.calibrator.calibrate(raw_conf, regime=regime, agreement_ratio=agreement_ratio)

        session.add(CalibratedPredictionRecord(
            symbol=symbol, agent="consensus",
            raw_confidence=calibrated.raw_confidence,
            calibrated_confidence=calibrated.calibrated_confidence,
            uncertainty=calibrated.uncertainty,
            reliability_score=calibrated.reliability_score,
            method=calibrated.method,
            decision=consensus.get("final_decision", "HOLD"),
        ))

        agent_preds = []
        for vote in consensus.get("agent_votes", []):
            if isinstance(vote, dict):
                agent_preds.append(AgentPrediction(
                    vote.get("agent", "unknown"), vote.get("decision", "HOLD"),
                    vote.get("confidence", 0.5), calibrated.calibrated_confidence,
                ))

        ensemble_result = self.ensemble.predict(agent_preds, regime=regime)

        session.add(EnsembleDecisionRecord(
            symbol=symbol, final_decision=ensemble_result.final_decision,
            meta_confidence=ensemble_result.meta_confidence,
            stacking_weights=ensemble_result.stacking_weights,
            agent_predictions=ensemble_result.agent_predictions,
            regime=regime, method=ensemble_result.method,
        ))

        market_state = self.similarity.extract_market_state(df, analysis.get("indicators", {}))
        similarity = self.similarity.find_similar(session, symbol, market_state)

        if not similarity.similar_scenarios:
            session.add(ScenarioEmbeddingRecord(
                symbol=symbol, scenario_label=f"state_{uuid.uuid4().hex[:8]}",
                embedding=self.similarity.build_embedding(market_state),
                market_state=market_state,
            ))

        adaptation = self.adaptive.adapt(
            regime, analysis.get("volatility", 50),
            risk.get("crash_probability", 0),
        )

        await self.temporal.store(session, MemoryContext(
            agent_name="quant_pipeline", symbol=symbol, memory_type="episodic",
            context={"regime": regime, "ensemble": ensemble_result.final_decision, "similarity": similarity.summary},
            decision=ensemble_result.final_decision,
        ))

        drift = self.performance_lab.detect_drift("consensus", [1, 1, 0, 1, 1], [1, 0, 0, 1, 1])

        self.event_bus.publish_sync(EventType.AI_DECISION, {
            "symbol": symbol, "decision": ensemble_result.final_decision,
            "calibrated_confidence": calibrated.calibrated_confidence,
        })

        gpu_status = self.gpu.get_status()

        elapsed = (time.perf_counter() - start) * 1000

        return {
            "calibration": asdict(calibrated),
            "ensemble": {
                "final_decision": ensemble_result.final_decision,
                "meta_confidence": ensemble_result.meta_confidence,
                "method": ensemble_result.method,
                "stacking_weights": ensemble_result.stacking_weights,
            },
            "similarity": {
                "summary": similarity.summary,
                "best_match": asdict(similarity.best_match) if similarity.best_match else None,
                "aggregate_probability": similarity.aggregate_probability,
                "scenarios": [asdict(s) for s in similarity.similar_scenarios[:3]],
            },
            "adaptive_strategy": {
                "reason": adaptation.reason,
                "config": adaptation.adjusted,
                "regime": adaptation.regime,
            },
            "drift": {
                "drift_score": drift.drift_score,
                "retrain_recommended": drift.retrain_recommended,
            },
            "gpu": asdict(gpu_status),
            "quant_elapsed_ms": round(elapsed, 1),
        }
