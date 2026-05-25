"""Buffer in-memory de eventos — fallback quando Redis offline + feed do Event Stream."""

from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

_buffer: deque[dict[str, Any]] = deque(maxlen=500)
_lock = Lock()


def append_event(event_type: str, payload: dict[str, Any], event_id: str | None = None) -> dict[str, Any]:
    entry = {
        "id": uuid.uuid4().hex[:12],
        "type": event_type,
        "event_id": event_id or str(uuid.uuid4()),
        "payload": payload,
        "ts": datetime.now(UTC).isoformat(),
    }
    with _lock:
        _buffer.appendleft(entry)
    return entry


def recent_events(limit: int = 20) -> list[dict[str, Any]]:
    with _lock:
        return list(_buffer)[:limit]
