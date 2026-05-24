"""CryptoGhost v3 - Temporal Memory System."""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.shared.ai_providers.factory import get_ai_provider
from backend.shared.logging_config import get_logger
from backend.shared.models_quant import TemporalMemoryRecord

logger = get_logger("cryptoghost.temporal_memory")


@dataclass
class MemoryContext:
    agent_name: str
    symbol: str
    memory_type: str
    context: dict
    decision: str | None = None


class TemporalMemorySystem:
    """Memória episódica, semântica e temporal multiagente."""

    MEMORY_TTL_HOURS = {"episodic": 168, "semantic": 720, "working": 1}

    def __init__(self) -> None:
        self._global_context: dict[str, list[dict]] = {}
        self._agent_memory: dict[str, list[dict]] = {}

    async def store(self, session: Session, mem: MemoryContext, outcome: str | None = None, outcome_pct: float | None = None) -> TemporalMemoryRecord:
        provider = get_ai_provider()
        context_text = f"{mem.symbol} {mem.agent_name} {mem.memory_type} {mem.context}"
        embedding = await provider.embed(context_text)

        ttl_hours = self.MEMORY_TTL_HOURS.get(mem.memory_type, 24)
        expires = datetime.now(UTC) + timedelta(hours=ttl_hours)

        record = TemporalMemoryRecord(
            agent_name=mem.agent_name,
            symbol=mem.symbol,
            memory_type=mem.memory_type,
            context=mem.context,
            embedding=embedding,
            decision=mem.decision,
            outcome=outcome,
            outcome_pct=outcome_pct,
            expires_at=expires,
        )
        session.add(record)
        session.flush()

        entry = {"context": mem.context, "decision": mem.decision, "embedding": embedding, "timestamp": datetime.now(UTC).isoformat()}
        self._agent_memory.setdefault(mem.agent_name, []).append(entry)
        self._global_context.setdefault(mem.symbol, []).append(entry)

        logger.debug("temporal_memory_stored", agent=mem.agent_name, type=mem.memory_type)
        return record

    def recall_agent(self, agent_name: str, limit: int = 10) -> list[dict]:
        return self._agent_memory.get(agent_name, [])[-limit:]

    def recall_global(self, symbol: str, limit: int = 20) -> list[dict]:
        return self._global_context.get(symbol, [])[-limit:]

    def recall_similar(self, session: Session, embedding: list[float], agent_name: str | None = None, limit: int = 5) -> list[TemporalMemoryRecord]:
        query = session.query(TemporalMemoryRecord).filter(
            TemporalMemoryRecord.expires_at > datetime.now(UTC)
        )
        if agent_name:
            query = query.filter(TemporalMemoryRecord.agent_name == agent_name)

        records = query.order_by(TemporalMemoryRecord.created_at.desc()).limit(200).all()
        scored = []
        for rec in records:
            if rec.embedding:
                sim = self._cosine(embedding, rec.embedding)
                scored.append((sim, rec))
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]

    def get_shared_context(self, symbol: str, agents: list[str]) -> dict:
        context = {"symbol": symbol, "agents": {}}
        for agent in agents:
            memories = [m for m in self._agent_memory.get(agent, []) if m.get("context", {}).get("symbol") == symbol]
            if memories:
                context["agents"][agent] = memories[-3:]
        return context

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        min_len = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(min_len))
        na = math.sqrt(sum(x * x for x in a[:min_len])) or 1
        nb = math.sqrt(sum(x * x for x in b[:min_len])) or 1
        return dot / (na * nb)
