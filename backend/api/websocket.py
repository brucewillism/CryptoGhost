"""CryptoGhost - WebSocket para atualizações em tempo real."""

import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.shared.logging_config import get_logger
from backend.shared.metrics import WEBSOCKET_CONNECTIONS

logger = get_logger("cryptoghost.websocket")
router = APIRouter()


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
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data == "subscribe:intelligence":
                await websocket.send_json({"type": "subscribed", "channel": "intelligence"})
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


async def broadcast_system_status() -> None:
    """Broadcast periódico de status do sistema."""
    from backend.risk_management.manager import RiskManager
    from backend.shared.config import get_settings

    while True:
        settings = get_settings()
        manager_risk = RiskManager()
        await manager.broadcast(
            {
                "type": "system_status",
                "data": {
                    "paper_trading": settings.paper_trading,
                    "risk": manager_risk.get_status(),
                    "connections": len(manager.active_connections),
                },
            }
        )
        await asyncio.sleep(5)
