"""SignalFreshnessValidator — rejeita sinais expirados."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import SignalStaleError
from backend.app.core.types import ConsensusResultV3
from backend.shared.config import get_settings
from backend.shared.models_v6 import MarketSignalV6Record


class SignalFreshnessValidator:
    def __init__(self) -> None:
        self.settings = get_settings()

    def validate_result(self, result: ConsensusResultV3) -> tuple[bool, str]:
        if result.expires_at and datetime.now(UTC) > result.expires_at:
            return False, "Signal expired"
        if not result.can_execute:
            reasons = ", ".join(result.rejection_reasons) or "consensus rejected"
            return False, reasons
        return True, "OK"

    async def get_fresh_signal(
        self,
        session: AsyncSession,
        symbol: str,
    ) -> MarketSignalV6Record | None:
        cutoff = datetime.now(UTC)
        result = await session.execute(
            select(MarketSignalV6Record)
            .where(
                MarketSignalV6Record.symbol == symbol,
                MarketSignalV6Record.can_execute == True,  # noqa: E712
            )
            .order_by(MarketSignalV6Record.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        if row.expires_at and row.expires_at < cutoff:
            raise SignalStaleError(f"Signal for {symbol} expired at {row.expires_at}")
        return row

    async def persist_signal(self, session: AsyncSession, result: ConsensusResultV3, regime: str) -> MarketSignalV6Record:
        from dataclasses import asdict

        record = MarketSignalV6Record(
            symbol=result.symbol,
            final_score=result.final_score,
            classification=result.classification.value,
            final_decision=result.final_decision,
            consensus=result.consensus,
            calibrated_confidence=result.calibrated_confidence,
            technical_score=result.technical_score,
            sentiment_score=result.sentiment_score,
            regime_alignment=result.regime_alignment,
            agreement=result.agreement,
            disagreement=result.disagreement,
            conflicts=result.conflicts,
            agent_votes=[asdict(v) for v in result.agent_votes],
            can_execute=result.can_execute,
            rejection_reasons=result.rejection_reasons,
            regime=regime,
            expires_at=result.expires_at,
        )
        session.add(record)
        await session.flush()
        return record
