"""StreamManager — skeleton para feeds WebSocket de mercado (fase futura)."""

from typing import Any, Callable

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.websocket")


class StreamManager:
    """Gerencia subscrições de ticker/trades; integração CCXT WS pendente."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, Callable[[dict[str, Any]], None]] = {}

    def subscribe(self, symbol: str, callback: Callable[[dict[str, Any]], None]) -> None:
        self._subscriptions[symbol] = callback
        logger.info("ws_subscribe", symbol=symbol, active=len(self._subscriptions))

    def unsubscribe(self, symbol: str) -> None:
        self._subscriptions.pop(symbol, None)

    def publish(self, symbol: str, payload: dict[str, Any]) -> None:
        cb = self._subscriptions.get(symbol)
        if cb:
            cb(payload)

    @property
    def active_symbols(self) -> list[str]:
        return list(self._subscriptions.keys())
