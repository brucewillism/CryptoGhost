"""CryptoGhost - Sistema de Notificações."""

import httpx

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.notifications")


class NotificationService:
    """Envia alertas críticos via webhook e email."""

    def __init__(self):
        self.settings = get_settings()

    async def send_alert(self, title: str, message: str, severity: str = "warning") -> bool:
        logger.info("notification_sent", title=title, severity=severity)
        if self.settings.notification_webhook:
            await self._send_webhook(title, message, severity)
        return True

    async def send_critical(self, message: str) -> bool:
        return await self.send_alert("CryptoGhost - ALERTA CRÍTICO", message, "critical")

    async def _send_webhook(self, title: str, message: str, severity: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    self.settings.notification_webhook,
                    json={"title": title, "message": message, "severity": severity, "source": "CryptoGhost"},
                )
        except Exception as exc:
            logger.error("webhook_failed", error=str(exc))
