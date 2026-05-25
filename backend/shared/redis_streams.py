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
        from backend.shared.live_events import append_event

        client = sync_redis.from_url(
            self._redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
        )
        try:
            message_id = client.xadd(
                STREAM_KEY,
                {"type": event_type, "data": json.dumps(payload, default=str)},
                maxlen=MAX_STREAM_LEN,
                approximate=True,
            )
            append_event(event_type, payload, message_id)
            logger.debug("stream_published", event_type=event_type, message_id=message_id)
            return message_id
        except Exception as exc:
            entry = append_event(event_type, payload)
            logger.debug("stream_publish_fallback", event_type=event_type, error=str(exc))
            return entry["id"]
        finally:
            client.close()

    async def publish(self, event_type: str, payload: dict[str, Any]) -> str:
        from backend.shared.live_events import append_event

        client = aioredis.from_url(
            self._redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
        )
        try:
            message_id = await client.xadd(
                STREAM_KEY,
                {"type": event_type, "data": json.dumps(payload, default=str)},
                maxlen=MAX_STREAM_LEN,
                approximate=True,
            )
            append_event(event_type, payload, message_id)
            return message_id
        except Exception as exc:
            entry = append_event(event_type, payload)
            logger.debug("stream_publish_async_fallback", event_type=event_type, error=str(exc))
            return entry["id"]
        finally:
            await client.aclose()


def get_stream_publisher() -> RedisStreamPublisher:
    return RedisStreamPublisher()
