"""CryptoGhost - Redis Streams para eventos de IA em tempo real."""

import json
from typing import Any

import redis.asyncio as aioredis
import redis as sync_redis

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.redis_streams")

STREAM_KEY = "cryptoghost:ai:events"
MAX_STREAM_LEN = 10000


class RedisStreamPublisher:
    """Publica eventos de inteligência para consumo WebSocket."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis_url = settings.redis_url

    def publish_sync(self, event_type: str, payload: dict[str, Any]) -> str:
        client = sync_redis.from_url(self._redis_url, decode_responses=True)
        try:
            message_id = client.xadd(
                STREAM_KEY,
                {"type": event_type, "data": json.dumps(payload, default=str)},
                maxlen=MAX_STREAM_LEN,
                approximate=True,
            )
            logger.debug("stream_published", event_type=event_type, message_id=message_id)
            return message_id
        finally:
            client.close()

    async def publish(self, event_type: str, payload: dict[str, Any]) -> str:
        client = aioredis.from_url(self._redis_url, decode_responses=True)
        try:
            message_id = await client.xadd(
                STREAM_KEY,
                {"type": event_type, "data": json.dumps(payload, default=str)},
                maxlen=MAX_STREAM_LEN,
                approximate=True,
            )
            return message_id
        finally:
            await client.aclose()


def get_stream_publisher() -> RedisStreamPublisher:
    return RedisStreamPublisher()
