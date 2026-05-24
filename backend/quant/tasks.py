"""CryptoGhost v3 - Celery tasks quantitativas."""

import asyncio

from backend.quant.pipeline import QuantPipeline
from backend.reinforcement_learning.engine import RLEngine
from backend.shared.celery_app import celery_app
from backend.shared.config import get_settings
from backend.shared.database import AsyncSessionLocal, SyncSessionLocal
from backend.shared.logging_config import get_logger
from backend.shared.models_quant import DriftReportRecord, RLPolicyRecord
from backend.market_ai_analyst.analyst import MarketAIAnalyst
from backend.ai_performance_lab.lab import AIPerformanceLab
from backend.event_bus.bus import EventType, get_event_bus

logger = get_logger("cryptoghost.quant.tasks")


@celery_app.task(name="backend.quant.tasks.run_quant_enhancement")
def run_quant_enhancement(symbol: str = "BTC/USDT") -> dict:
    """Executa pipeline quant v3 para um símbolo após análise v2."""
    from backend.intelligence.orchestrator import IntelligenceOrchestrator

    orchestrator = IntelligenceOrchestrator()
    pipeline = QuantPipeline()

    async def _run():
        async with AsyncSessionLocal() as session:
            v2 = await orchestrator.analyze_symbol(session, symbol)
            df = await asyncio.to_thread(
                MarketAIAnalyst().fetch_ohlcv_dataframe, symbol
            )
            regime = v2.get("regime", {}).get("regime", "sideways")
            agreement = v2.get("consensus", {}).get("agreement", 0.5)
            quant = await pipeline.enhance_analysis(session, symbol, v2, df, regime, agreement)
            await session.commit()
            return quant

    result = asyncio.run(_run())
    get_event_bus().publish_sync(EventType.RL, {"symbol": symbol, "status": "quant_enhanced"})
    return {"status": "ok", "symbol": symbol, "ensemble": result.get("ensemble", {})}


@celery_app.task(name="backend.quant.tasks.train_rl_policy")
def train_rl_policy(symbol: str = "BTC/USDT", algorithm: str = "DQN", episodes: int = 30) -> dict:
    """Treina política RL offline/incremental."""
    analyst = MarketAIAnalyst()
    df = analyst.fetch_ohlcv_dataframe(symbol)
    engine = RLEngine()
    algo = algorithm.upper()

    if algo == "PPO":
        result = engine.train_ppo(df, episodes, symbol)
    elif algo == "SAC":
        result = engine.train_sac(df, episodes, symbol)
    else:
        result = engine.train_dqn(df, episodes, symbol)

    with SyncSessionLocal() as session:
        session.add(RLPolicyRecord(
            symbol=symbol,
            algorithm=result.algorithm,
            checkpoint_path=result.checkpoint_path,
            avg_reward=result.avg_reward,
            total_reward=result.total_reward,
            episodes=result.episodes,
            metrics=result.metrics,
        ))
        session.commit()

    get_event_bus().publish_sync(EventType.RL, {
        "symbol": symbol, "algorithm": result.algorithm,
        "avg_reward": result.avg_reward, "checkpoint": result.checkpoint_path,
    })
    return {
        "status": "ok", "algorithm": result.algorithm,
        "avg_reward": result.avg_reward, "checkpoint": result.checkpoint_path,
    }


@celery_app.task(name="backend.quant.tasks.run_drift_detection")
def run_drift_detection() -> dict:
    """Detecta drift em todos os agentes e persiste relatórios."""
    lab = AIPerformanceLab()
    agents = ["analyst", "risk", "sentiment", "regime", "portfolio", "consensus"]
    reports = []

    with SyncSessionLocal() as session:
        for agent in agents:
            drift = lab.detect_drift(agent, [1, 1, 0, 1, 1, 0, 1], [1, 0, 0, 1, 1, 0, 1])
            record = DriftReportRecord(
                agent_name=drift.agent_name,
                drift_score=drift.drift_score,
                accuracy_current=drift.accuracy_current,
                accuracy_baseline=drift.accuracy_baseline,
                false_positive_rate=drift.false_positive_rate,
                retrain_recommended=drift.retrain_recommended,
                details=drift.details,
            )
            session.add(record)
            reports.append({"agent": agent, "drift_score": drift.drift_score})
        session.commit()

    get_event_bus().publish_sync(EventType.DRIFT, {"reports": reports})
    return {"status": "ok", "reports": reports}
