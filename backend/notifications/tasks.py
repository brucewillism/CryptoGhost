"""CryptoGhost - Celery tasks de notificações."""

import asyncio

from backend.notifications.service import NotificationService
from backend.shared.celery_app import celery_app


@celery_app.task(name="backend.notifications.tasks.send_alert")
def send_alert(title: str, message: str, severity: str = "warning") -> dict:
    service = NotificationService()
    asyncio.run(service.send_alert(title, message, severity))
    return {"status": "sent"}
