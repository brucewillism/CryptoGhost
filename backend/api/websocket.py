"""CryptoGhost - WebSocket para atualizações em tempo real."""

import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.shared.logging_config import get_logger
from backend.shared.metrics import WEBSOCKET_CONNECTIONS

logger = get_logger("cryptoghost.websocket")
router = APIRouter()

BROADCAST_INTERVAL_SEC = 5


class ConnectionManager:
    """Gerencia conexões WebSocket ativas."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        WEBSOCKET_CONNECTIONS.set(len(self.active_connections))
        logger.info("ws_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        WEBSOCKET_CONNECTIONS.set(len(self.active_connections))
        logger.info("ws_disconnected", total=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()
_broadcast_task: asyncio.Task | None = None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data in ("subscribe:intelligence", "subscribe:dashboard", "subscribe:all"):
                await websocket.send_json({"type": "subscribed", "channel": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_market_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "market_update", "data": data})


async def broadcast_intelligence_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "intelligence_update", "data": data})


async def broadcast_sentiment_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "sentiment_update", "data": data})


async def broadcast_consensus_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "consensus_update", "data": data})


async def broadcast_quant_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "quant_update", "data": data})


async def broadcast_dashboard_update(data: dict[str, Any]) -> None:
    await manager.broadcast({"type": "dashboard_update", "data": data})


async def _realtime_broadcast_loop() -> None:
    """Envia snapshot do dashboard a cada N segundos para todos os clientes."""
    from backend.api.services.live_dashboard import build_live_snapshot
    from backend.shared.database import AsyncSessionLocal

    while True:
        try:
            if manager.active_connections:
                async with AsyncSessionLocal() as session:
                    snapshot = await build_live_snapshot(session)
                await broadcast_dashboard_update(snapshot)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("realtime_broadcast_failed", error=str(exc))
        await asyncio.sleep(BROADCAST_INTERVAL_SEC)


def start_realtime_broadcasts() -> asyncio.Task:
    global _broadcast_task
    if _broadcast_task is None or _broadcast_task.done():
        _broadcast_task = asyncio.create_task(_realtime_broadcast_loop())
    return _broadcast_task


async def stop_realtime_broadcasts() -> None:
    global _broadcast_task
    if _broadcast_task and not _broadcast_task.done():
        _broadcast_task.cancel()
        try:
            await _broadcast_task
        except asyncio.CancelledError:
            pass
    _broadcast_task = None
