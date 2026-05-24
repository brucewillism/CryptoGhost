"""CryptoGhost v3 - Event Bus (Event-Driven Architecture)."""

from enum import Enum
from typing import Any, Callable
from uuid import uuid4

import redis.asyncio as aioredis
import redis as sync_redis

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.event_bus")

STREAM_PREFIX = "cryptoghost:events"
DLQ_STREAM = "cryptoghost:events:dlq"
PUBSUB_CHANNEL = "cryptoghost:events:broadcast"
MAX_RETRIES = 3


class EventType(str, Enum):
    MARKET = "market_event"
    SENTIMENT = "sentiment_event"
    AI_DECISION = "ai_decision_event"
    RISK = "risk_event"
    MACRO = "macro_event"
    TRADE = "trade_event"
    ANOMALY = "anomaly_event"
    FEATURE = "feature_event"
    RL = "rl_event"
    DRIFT = "drift_event"


class EventBus:
    """Barramento de eventos com Redis Streams, Pub/Sub, retry e DLQ."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis_url = settings.redis_url
        self._handlers: dict[str, list[Callable[[dict], Any]]] = {}

    def subscribe(self, event_type: EventType | str, handler: Callable[[dict], Any]) -> None:
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._handlers.setdefault(key, []).append(handler)

    def publish_sync(self, event_type: EventType | str, payload: dict[str, Any]) -> str:
        import json

        client = sync_redis.from_url(self._redis_url, decode_responses=True)
        event_id = str(uuid4())
        etype = event_type.value if isinstance(event_type, EventType) else event_type
        stream = f"{STREAM_PREFIX}:{etype}"

        try:
            msg_id = client.xadd(
                stream,
                {"event_id": event_id, "type": etype, "payload": json.dumps(payload, default=str)},
                maxlen=50000,
                approximate=True,
            )
            client.publish(PUBSUB_CHANNEL, json.dumps({"event_id": event_id, "type": etype}))
            self._dispatch_sync(etype, {"event_id": event_id, "type": etype, "payload": payload})
            logger.debug("event_published", event_type=etype, event_id=event_id)
            return event_id
        except Exception as exc:
            logger.error("event_publish_failed", error=str(exc))
            client.xadd(DLQ_STREAM, {"event_id": event_id, "type": etype, "error": str(exc)})
            raise
        finally:
            client.close()

    async def publish(self, event_type: EventType | str, payload: dict[str, Any]) -> str:
        import json

        client = aioredis.from_url(self._redis_url, decode_responses=True)
        event_id = str(uuid4())
        etype = event_type.value if isinstance(event_type, EventType) else event_type
        stream = f"{STREAM_PREFIX}:{etype}"

        try:
            await client.xadd(
                stream,
                {"event_id": event_id, "type": etype, "payload": json.dumps(payload, default=str)},
                maxlen=50000,
                approximate=True,
            )
            await client.publish(PUBSUB_CHANNEL, json.dumps({"event_id": event_id, "type": etype}))
            return event_id
        finally:
            await client.aclose()

    def _dispatch_sync(self, event_type: str, event: dict) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as exc:
                logger.error("event_handler_failed", event_type=event_type, error=str(exc))

    def consume_with_retry(self, event_type: EventType, handler: Callable[[dict], bool]) -> int:
        import json

        client = sync_redis.from_url(self._redis_url, decode_responses=True)
        stream = f"{STREAM_PREFIX}:{event_type.value}"
        group = "cryptoghost_consumers"
        consumer = f"worker-{uuid4().hex[:8]}"

        try:
            client.xgroup_create(stream, group, id="0", mkstream=True)
        except sync_redis.ResponseError:
            pass

        processed = 0
        messages = client.xreadgroup(group, consumer, {stream: ">"}, count=10, block=1000)

        for _stream, entries in messages:
            for msg_id, data in entries:
                payload = json.loads(data.get("payload", "{}"))
                event = {"event_id": data.get("event_id"), "type": event_type.value, "payload": payload}
                try:
                    success = handler(event)
                    if success:
                        client.xack(stream, group, msg_id)
                        processed += 1
                    else:
                        retry = int(data.get("retry_count", 0)) + 1
                        if retry >= MAX_RETRIES:
                            client.xadd(DLQ_STREAM, {"original_id": msg_id, "payload": data.get("payload", "")})
                            client.xack(stream, group, msg_id)
                        else:
                            client.xadd(stream, {**data, "retry_count": str(retry)})
                except Exception as exc:
                    logger.error("event_consume_error", error=str(exc))
                    client.xadd(DLQ_STREAM, {"original_id": msg_id, "error": str(exc)})
                    client.xack(stream, group, msg_id)

        client.close()
        return processed


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
