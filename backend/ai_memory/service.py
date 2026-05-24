"""CryptoGhost - AI Memory (Semantic Memory)."""

import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.shared.ai_providers.factory import get_ai_provider
from backend.shared.logging_config import get_logger
from backend.shared.models_intelligence import AIMemoryRecord

logger = get_logger("cryptoghost.ai_memory")


@dataclass
class MemoryEntry:
    symbol: str
    decision: str
    market_context: dict
    embedding: list[float]
    outcome: str | None = None
    performance_pct: float | None = None
    was_correct: bool | None = None
    lesson: str | None = None


@dataclass
class MemoryInsight:
    similar_decisions: list[dict]
    historical_accuracy: float
    lessons: list[str]
    recommendation_adjustment: str


class AIMemoryService:
    """Memória semântica com embeddings para aprendizado contextual."""

    def __init__(self):
        self._provider = None

    async def _get_provider(self):
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    async def create_embedding(self, text: str) -> list[float]:
        provider = await self._get_provider()
        return await provider.embed(text)

    async def store(self, session: Session, entry: MemoryEntry) -> AIMemoryRecord:
        context_text = f"{entry.symbol} {entry.decision} {entry.market_context}"
        if not entry.embedding:
            entry.embedding = await self.create_embedding(context_text)

        record = AIMemoryRecord(
            symbol=entry.symbol,
            decision=entry.decision,
            outcome=entry.outcome,
            performance_pct=entry.performance_pct,
            market_context=entry.market_context,
            embedding=entry.embedding,
            was_correct=entry.was_correct,
            lesson=entry.lesson,
        )
        session.add(record)
        session.flush()
        logger.info("memory_stored", symbol=entry.symbol, decision=entry.decision)
        return record

    def recall_similar(self, session: Session, embedding: list[float], symbol: str | None = None, limit: int = 10) -> list[AIMemoryRecord]:
        query = session.query(AIMemoryRecord)
        if symbol:
            query = query.filter(AIMemoryRecord.symbol == symbol)
        records = query.order_by(AIMemoryRecord.created_at.desc()).limit(100).all()

        scored = []
        for record in records:
            if record.embedding:
                sim = self._cosine_similarity(embedding, record.embedding)
                scored.append((sim, record))

        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]

    def get_insights(self, session: Session, symbol: str) -> MemoryInsight:
        records = session.query(AIMemoryRecord).filter(AIMemoryRecord.symbol == symbol).limit(50).all()

        if not records:
            return MemoryInsight([], 0.5, ["Sem histórico — usar cautela"], "neutral")

        evaluated = [r for r in records if r.was_correct is not None]
        accuracy = sum(1 for r in evaluated if r.was_correct) / max(len(evaluated), 1)

        lessons = [r.lesson for r in records if r.lesson][-5:]
        if accuracy < 0.4:
            adjustment = "reduce_confidence"
        elif accuracy > 0.7:
            adjustment = "increase_confidence"
        else:
            adjustment = "neutral"

        similar = [
            {"decision": r.decision, "outcome": r.outcome, "performance": r.performance_pct, "correct": r.was_correct}
            for r in records[:5]
        ]

        return MemoryInsight(similar, round(accuracy, 2), lessons or ["Análise histórica limitada"], adjustment)

    async def update_outcome(self, session: Session, record_id: Any, outcome: str, performance_pct: float, was_correct: bool) -> None:
        record = session.get(AIMemoryRecord, record_id)
        if record:
            record.outcome = outcome
            record.performance_pct = performance_pct
            record.was_correct = was_correct
            record.lesson = self._generate_lesson(record.decision, outcome, was_correct, performance_pct)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            min_len = min(len(a), len(b))
            a, b = a[:min_len], b[:min_len]
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1
        norm_b = math.sqrt(sum(x * x for x in b)) or 1
        return dot / (norm_a * norm_b)

    @staticmethod
    def _generate_lesson(decision: str, outcome: str, correct: bool, perf: float) -> str:
        if correct:
            return f"Decisão {decision} correta ({perf:+.1f}%) — reforçar padrão similar"
        return f"Decisão {decision} incorreta ({perf:+.1f}%) — revisar condições de mercado antes de repetir"
