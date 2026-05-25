"""AgentPerformanceService — pesos dinâmicos por agente/regime/ativo."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_consensus_engine.consensus import AGENT_WEIGHTS
from backend.shared.logging_config import get_logger
from backend.shared.models_v5 import PredictionValidationRecord
from backend.shared.models_v6 import AgentPerformanceRecord

logger = get_logger("cryptoghost.v6.meta_learning")

DEFAULT_AGENTS = list(AGENT_WEIGHTS.keys())


class AgentPerformanceService:
    async def compute_weights(
        self,
        session: AsyncSession,
        symbol: str,
        regime: str,
    ) -> dict[str, float]:
        """Retorna pesos dinâmicos por agente; fallback para AGENT_WEIGHTS."""
        result = await session.execute(
            select(AgentPerformanceRecord).where(
                AgentPerformanceRecord.regime.in_([regime, "*"]),
                AgentPerformanceRecord.symbol.in_([symbol, "*"]),
            )
        )
        rows = result.scalars().all()
        if not rows:
            await self._seed_from_validations(session, symbol, regime)
            result = await session.execute(
                select(AgentPerformanceRecord).where(
                    AgentPerformanceRecord.regime.in_([regime, "*"]),
                )
            )
            rows = result.scalars().all()

        weights = dict(AGENT_WEIGHTS)
        acc_map: dict[str, float] = {}
        for row in rows:
            if row.agent_name in weights:
                weights[row.agent_name] = row.dynamic_weight
                acc_map[row.agent_name] = row.accuracy
                acc_map[f"{row.agent_name}_acc"] = row.accuracy

        weights.update(acc_map)
        return weights

    async def _seed_from_validations(
        self,
        session: AsyncSession,
        symbol: str,
        regime: str,
    ) -> None:
        val_r = await session.execute(
            select(PredictionValidationRecord)
            .where(PredictionValidationRecord.symbol == symbol)
            .order_by(PredictionValidationRecord.created_at.desc())
            .limit(50)
        )
        validations = val_r.scalars().all()
        base_acc = 0.5
        if validations:
            base_acc = sum(1 for v in validations if v.direction_correct) / len(validations)

        for agent in DEFAULT_AGENTS:
            session.add(AgentPerformanceRecord(
                agent_name=agent,
                symbol=symbol,
                regime=regime,
                accuracy=base_acc,
                sample_count=len(validations),
                dynamic_weight=AGENT_WEIGHTS.get(agent, 0.2) * (0.8 + 0.4 * base_acc),
            ))

    async def update_from_validation(
        self,
        session: AsyncSession,
        agent_name: str,
        symbol: str,
        regime: str,
        was_correct: bool,
    ) -> None:
        result = await session.execute(
            select(AgentPerformanceRecord).where(
                AgentPerformanceRecord.agent_name == agent_name,
                AgentPerformanceRecord.symbol == symbol,
                AgentPerformanceRecord.regime == regime,
            ).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            row = AgentPerformanceRecord(
                agent_name=agent_name, symbol=symbol, regime=regime,
                accuracy=0.5, sample_count=0, dynamic_weight=AGENT_WEIGHTS.get(agent_name, 0.2),
            )
            session.add(row)

        row.sample_count += 1
        delta = 1.0 if was_correct else 0.0
        row.accuracy = ((row.accuracy * (row.sample_count - 1)) + delta) / row.sample_count
        row.dynamic_weight = AGENT_WEIGHTS.get(agent_name, 0.2) * (0.7 + 0.6 * row.accuracy)
