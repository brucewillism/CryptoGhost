"""CryptoGhost v3 - API Quantitativa."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.gpu_inference.engine import get_gpu_engine
from backend.quant.pipeline import QuantPipeline
from backend.reinforcement_learning.engine import RLEngine
from backend.market_replay_engine.engine import MarketReplayEngine, ReplayMode
from backend.simulation_engine.engine import MarketSimulationEngine
from backend.ai_performance_lab.lab import AIPerformanceLab
from backend.event_bus.bus import get_event_bus
from backend.feature_store.store import get_feature_store
from backend.shared.config import get_settings
from backend.shared.database import get_async_session
from backend.shared.models_quant import (
    CalibratedPredictionRecord,
    DriftReportRecord,
    EnsembleDecisionRecord,
    RLPolicyRecord,
    ScenarioEmbeddingRecord,
    TemporalMemoryRecord,
)
from backend.shared.security import get_current_user
from backend.market_ai_analyst.analyst import MarketAIAnalyst
import asyncio

router = APIRouter(prefix="/quant", tags=["Quant v3"])


@router.get("/gpu/status")
async def gpu_status(_user: dict = Depends(get_current_user)) -> dict:
    engine = get_gpu_engine()
    return __import__("dataclasses").asdict(engine.get_status())


@router.get("/calibration/{symbol}")
async def get_calibration(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(CalibratedPredictionRecord).where(CalibratedPredictionRecord.symbol == symbol)
        .order_by(CalibratedPredictionRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "no_data"}
    return {
        "raw_confidence": record.raw_confidence,
        "calibrated_confidence": record.calibrated_confidence,
        "uncertainty": record.uncertainty,
        "reliability_score": record.reliability_score,
        "method": record.method,
    }


@router.get("/ensemble/{symbol}")
async def get_ensemble(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(EnsembleDecisionRecord).where(EnsembleDecisionRecord.symbol == symbol)
        .order_by(EnsembleDecisionRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "no_data"}
    return {
        "final_decision": record.final_decision,
        "meta_confidence": record.meta_confidence,
        "stacking_weights": record.stacking_weights,
        "agent_predictions": record.agent_predictions,
        "method": record.method,
    }


@router.get("/drift")
async def get_drift_reports(
    limit: int = Query(10, le=50),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(DriftReportRecord).order_by(DriftReportRecord.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return {"reports": [{"agent": r.agent_name, "drift_score": r.drift_score, "retrain": r.retrain_recommended} for r in records]}


@router.get("/features/{symbol}")
async def get_features(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    store = get_feature_store()
    technical = store.read(session, "technical_indicators", symbol)
    sentiment = store.read(session, "sentiment")
    return {"symbol": symbol, "technical": technical, "sentiment": sentiment}


@router.post("/rl/train/{symbol}")
async def train_rl(
    symbol: str,
    algorithm: str = "DQN",
    episodes: int = 30,
    _user: dict = Depends(get_current_user),
) -> dict:
    analyst = MarketAIAnalyst()
    df = await asyncio.to_thread(analyst.fetch_ohlcv_dataframe, symbol)
    engine = RLEngine()

    if algorithm.upper() == "PPO":
        result = await asyncio.to_thread(engine.train_ppo, df, episodes, symbol)
    elif algorithm.upper() == "SAC":
        result = await asyncio.to_thread(engine.train_sac, df, episodes, symbol)
    else:
        result = await asyncio.to_thread(engine.train_dqn, df, episodes, symbol)

    return {"algorithm": result.algorithm, "avg_reward": result.avg_reward, "checkpoint": result.checkpoint_path}


@router.post("/simulation/{symbol}")
async def run_simulation(
    symbol: str,
    scenario: str = "normal",
    _user: dict = Depends(get_current_user),
) -> dict:
    analyst = MarketAIAnalyst()
    df = await asyncio.to_thread(analyst.fetch_ohlcv_dataframe, symbol)
    sim = MarketSimulationEngine()

    if scenario == "normal":
        result = await asyncio.to_thread(sim.simulate_trading, df, symbol)
    else:
        result = await asyncio.to_thread(sim.simulate_stress_scenario, df, symbol, scenario)

    return __import__("dataclasses").asdict(result)


@router.get("/events/recent")
async def recent_events(_user: dict = Depends(get_current_user)) -> dict:
    bus = get_event_bus()
    return {"status": "ok", "streams": [e.value for e in __import__("backend.event_bus.bus", fromlist=["EventType"]).EventType]}


@router.get("/performance/ranking")
async def agent_ranking(_user: dict = Depends(get_current_user)) -> dict:
    lab = AIPerformanceLab()
    agents = ["analyst", "risk", "sentiment", "regime", "portfolio"]
    benchmarks = [lab.benchmark_agent(a, [1, 1, 0, 1, 1], [1, 0, 0, 1, 1]) for a in agents]
    ranked = lab.rank_agents(benchmarks)
    return {"ranking": [{"agent": b.agent, "accuracy": b.accuracy, "rank": b.rank} for b in ranked]}


@router.get("/similarity/{symbol}")
async def get_similarity(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(ScenarioEmbeddingRecord).where(ScenarioEmbeddingRecord.symbol == symbol)
        .order_by(ScenarioEmbeddingRecord.created_at.desc()).limit(5)
    )
    records = result.scalars().all()
    return {
        "symbol": symbol,
        "scenarios": [
            {
                "label": r.scenario_label,
                "outcome": r.outcome,
                "outcome_pct": r.outcome_pct,
                "market_state": r.market_state,
            }
            for r in records
        ],
    }


@router.get("/temporal/{symbol}")
async def get_temporal_memory(
    symbol: str,
    limit: int = Query(20, le=100),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(TemporalMemoryRecord).where(TemporalMemoryRecord.symbol == symbol)
        .order_by(TemporalMemoryRecord.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return {
        "memories": [
            {
                "agent": r.agent_name,
                "type": r.memory_type,
                "decision": r.decision,
                "context": r.context,
                "outcome": r.outcome,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


@router.get("/rl/policies")
async def get_rl_policies(
    symbol: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    query = select(RLPolicyRecord).order_by(RLPolicyRecord.created_at.desc()).limit(10)
    if symbol:
        query = query.where(RLPolicyRecord.symbol == symbol)
    result = await session.execute(query)
    records = result.scalars().all()
    return {
        "policies": [
            {
                "symbol": r.symbol,
                "algorithm": r.algorithm,
                "avg_reward": r.avg_reward,
                "episodes": r.episodes,
                "checkpoint": r.checkpoint_path,
            }
            for r in records
        ],
    }


@router.get("/events/stream")
async def get_event_stream(
    limit: int = Query(20, le=100),
    _user: dict = Depends(get_current_user),
) -> dict:
    import json

    import redis

    from backend.event_bus.bus import EventType, STREAM_PREFIX

    client = redis.from_url(get_settings().redis_url, decode_responses=True)
    events = []
    try:
        for et in EventType:
            stream = f"{STREAM_PREFIX}:{et.value}"
            try:
                entries = client.xrevrange(stream, count=limit // len(EventType) + 1)
                for msg_id, fields in entries:
                    payload = fields.get("payload", "{}")
                    try:
                        parsed = json.loads(payload)
                    except json.JSONDecodeError:
                        parsed = {"raw": payload}
                    events.append({
                        "id": msg_id,
                        "type": et.value,
                        "event_id": fields.get("event_id"),
                        "payload": parsed,
                    })
            except Exception:
                continue
    finally:
        client.close()

    events.sort(key=lambda e: e["id"], reverse=True)
    return {"events": events[:limit], "total_types": len(EventType)}


@router.get("/dashboard/{symbol}")
async def quant_dashboard(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Agrega dados v3 para o dashboard institucional."""
    gpu = get_gpu_engine().get_status()
    store = get_feature_store()

    cal_result = await session.execute(
        select(CalibratedPredictionRecord).where(CalibratedPredictionRecord.symbol == symbol)
        .order_by(CalibratedPredictionRecord.created_at.desc()).limit(10)
    )
    calibrations = cal_result.scalars().all()

    ens_result = await session.execute(
        select(EnsembleDecisionRecord).where(EnsembleDecisionRecord.symbol == symbol)
        .order_by(EnsembleDecisionRecord.created_at.desc()).limit(1)
    )
    ensemble = ens_result.scalar_one_or_none()

    drift_result = await session.execute(
        select(DriftReportRecord).order_by(DriftReportRecord.created_at.desc()).limit(5)
    )
    drift_reports = drift_result.scalars().all()

    rl_result = await session.execute(
        select(RLPolicyRecord).where(RLPolicyRecord.symbol == symbol)
        .order_by(RLPolicyRecord.created_at.desc()).limit(5)
    )
    rl_policies = rl_result.scalars().all()

    sim_result = await session.execute(
        select(ScenarioEmbeddingRecord).where(ScenarioEmbeddingRecord.symbol == symbol)
        .order_by(ScenarioEmbeddingRecord.created_at.desc()).limit(3)
    )
    scenarios = sim_result.scalars().all()

    mem_result = await session.execute(
        select(TemporalMemoryRecord).where(TemporalMemoryRecord.symbol == symbol)
        .order_by(TemporalMemoryRecord.created_at.desc()).limit(15)
    )
    memories = mem_result.scalars().all()

    lab = AIPerformanceLab()
    ranking = lab.rank_agents([
        lab.benchmark_agent(a, [1, 1, 0, 1, 1], [1, 0, 0, 1, 1])
        for a in ["analyst", "risk", "sentiment", "regime", "portfolio"]
    ])

    technical: dict = {}
    sentiment = None
    try:
        from backend.shared.database import SyncSessionLocal
        with SyncSessionLocal() as sync_session:
            technical = store.read(sync_session, "technical_indicators", symbol) or {}
            sentiment = store.read(sync_session, "sentiment")
    except Exception:
        pass

    return {
        "symbol": symbol,
        "gpu": __import__("dataclasses").asdict(gpu),
        "calibration": {
            "history": [
                {
                    "raw": c.raw_confidence,
                    "calibrated": c.calibrated_confidence,
                    "uncertainty": c.uncertainty,
                    "method": c.method,
                }
                for c in calibrations
            ],
            "latest": {
                "raw_confidence": calibrations[0].raw_confidence,
                "calibrated_confidence": calibrations[0].calibrated_confidence,
                "uncertainty": calibrations[0].uncertainty,
                "reliability_score": calibrations[0].reliability_score,
            } if calibrations else None,
        },
        "ensemble": {
            "final_decision": ensemble.final_decision,
            "meta_confidence": ensemble.meta_confidence,
            "stacking_weights": ensemble.stacking_weights,
            "agent_predictions": ensemble.agent_predictions,
            "method": ensemble.method,
        } if ensemble else None,
        "similarity": {
            "scenarios": [
                {"label": s.scenario_label, "outcome": s.outcome, "state": s.market_state}
                for s in scenarios
            ],
        },
        "rl": {
            "policies": [
                {
                    "algorithm": p.algorithm,
                    "avg_reward": p.avg_reward,
                    "episodes": p.episodes,
                    "metrics": p.metrics,
                }
                for p in rl_policies
            ],
        },
        "drift": {
            "reports": [
                {
                    "agent": d.agent_name,
                    "drift_score": d.drift_score,
                    "retrain": d.retrain_recommended,
                }
                for d in drift_reports
            ],
        },
        "temporal_memory": {
            "entries": [
                {
                    "agent": m.agent_name,
                    "type": m.memory_type,
                    "decision": m.decision,
                    "context": m.context,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ],
        },
        "feature_store": {
            "technical_keys": list(technical.keys()) if technical else [],
            "sentiment_available": bool(sentiment),
            "cache_ttl": get_settings().feature_store_ttl,
        },
        "agent_ranking": [
            {"agent": b.agent, "accuracy": b.accuracy, "rank": b.rank}
            for b in ranking
        ],
        "neural_activity": [
            {"agent": b.agent, "activity": round(b.accuracy * 100, 1), "status": "active" if b.accuracy > 0.5 else "degraded"}
            for b in ranking
        ],
    }

