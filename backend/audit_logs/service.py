"""CryptoGhost - Módulo de Auditoria."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.logging_config import get_logger
from backend.shared.models import AuditEventType, AuditLog

logger = get_logger("cryptoghost.audit")


class AuditService:
    """Serviço centralizado de trilha de auditoria."""

    @staticmethod
    async def log(
        session: AsyncSession,
        event_type: AuditEventType,
        action: str,
        actor: str = "system",
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            event_type=event_type.value,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        session.add(entry)
        await session.flush()

        logger.info(
            "audit_event",
            event_type=event_type.value,
            action=action,
            actor=actor,
            resource_id=resource_id,
        )
        return entry

    @staticmethod
    async def log_order(session: AsyncSession, order_id: UUID, action: str, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.ORDER,
            action,
            resource_type="order",
            resource_id=str(order_id),
            details=details,
        )

    @staticmethod
    async def log_prediction(session: AsyncSession, prediction_id: UUID, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.PREDICTION,
            "ai_prediction_generated",
            resource_type="prediction",
            resource_id=str(prediction_id),
            details=details,
        )

    @staticmethod
    async def log_decision(session: AsyncSession, action: str, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.DECISION,
            action,
            details=details,
        )

    @staticmethod
    async def log_risk_event(session: AsyncSession, action: str, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.RISK,
            action,
            details=details,
        )

    @staticmethod
    async def log_error(session: AsyncSession, action: str, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.ERROR,
            action,
            details=details,
        )

    @staticmethod
    async def log_financial(session: AsyncSession, action: str, details: dict) -> AuditLog:
        return await AuditService.log(
            session,
            AuditEventType.FINANCIAL,
            action,
            details=details,
        )
