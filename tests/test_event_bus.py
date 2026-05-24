"""Testes do Event Bus v3."""

from unittest.mock import MagicMock, patch

from backend.event_bus.bus import EventBus, EventType


def test_event_type_values():
    assert EventType.MARKET.value == "market_event"
    assert EventType.AI_DECISION.value == "ai_decision_event"
    assert len(EventType) >= 7


def test_subscribe_and_dispatch():
    bus = EventBus()
    received = []
    bus.subscribe(EventType.RISK, lambda e: received.append(e))
    bus._dispatch_sync(EventType.RISK.value, {"type": "risk_event", "payload": {"level": "high"}})
    assert len(received) == 1
    assert received[0]["payload"]["level"] == "high"


@patch("backend.event_bus.bus.sync_redis.from_url")
def test_publish_sync(mock_redis):
    client = MagicMock()
    client.xadd.return_value = "1234-0"
    mock_redis.return_value = client

    bus = EventBus()
    event_id = bus.publish_sync(EventType.TRADE, {"symbol": "BTC/USDT", "side": "buy"})
    assert event_id
    client.xadd.assert_called_once()
    client.publish.assert_called_once()
