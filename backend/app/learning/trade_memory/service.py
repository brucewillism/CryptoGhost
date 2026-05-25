"""TradeMemoryService — histórico de trades para aprendizado."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.logging_config import get_logger
from backend.shared.models import Order
from backend.shared.models_v6 import TradeMemoryEmbeddingRecord, TradeMemoryRecord

logger = get_logger("cryptoghost.v6.trade_memory")


class TradeMemoryService:
    async def record_open(
        self,
        session: AsyncSession,
        order: Order,
        consensus: dict[str, Any],
        regime: str = "unknown",
        features: dict[str, float] | None = None,
    ) -> TradeMemoryRecord:
        record = TradeMemoryRecord(
            asset=order.symbol,
            regime=regime,
            setup=consensus.get("classification", "unknown"),
            entry_price=float(order.average_price or order.price or 0),
            confidence=float(consensus.get("calibrated_confidence", 0.5)),
            consensus=float(consensus.get("consensus", 0.5)),
            features_snapshot=features or {},
            result="open",
            market_conditions={"final_score": consensus.get("final_score")},
            order_id=str(order.id),
        )
        session.add(record)
        await session.flush()
        await self._store_embedding(session, record)
        return record

    async def record_close(
        self,
        session: AsyncSession,
        order_id: str,
        exit_price: float,
        pnl: float,
        duration_hours: float,
    ) -> TradeMemoryRecord | None:
        result = await session.execute(
            select(TradeMemoryRecord).where(TradeMemoryRecord.order_id == order_id).limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            return None
        record.exit_price = exit_price
        record.pnl = pnl
        record.duration_hours = duration_hours
        record.result = "profit" if pnl > 0 else "loss"
        return record

    async def find_similar(
        self,
        session: AsyncSession,
        asset: str,
        features: dict[str, float],
        limit: int = 5,
    ) -> list[TradeMemoryRecord]:
        result = await session.execute(
            select(TradeMemoryRecord)
            .where(TradeMemoryRecord.asset == asset, TradeMemoryRecord.result.in_(["profit", "loss"]))
            .order_by(TradeMemoryRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _store_embedding(self, session: AsyncSession, record: TradeMemoryRecord) -> None:
        try:
            text = json.dumps(record.features_snapshot, default=str)[:500]
            embedding = self._simple_embed(text)
            session.add(TradeMemoryEmbeddingRecord(
                trade_memory_id=record.id,
                embedding=embedding,
                label=record.setup,
            ))
        except Exception as exc:
            logger.debug("embedding_skip", error=str(exc))

    @staticmethod
    def _simple_embed(text: str, dim: int = 32) -> list[float]:
        """Fallback embedding when pgvector/Ollama unavailable."""
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        return [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(dim)]
