"""Cadeia de fallback entre providers."""

from typing import Any

from backend.app.core.exceptions import DataProviderError
from backend.app.data.providers.base import BaseDataProvider
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.providers")


class FallbackChain:
    def __init__(self, providers: list[BaseDataProvider]) -> None:
        self.providers = providers

    def fetch(self, symbol: str, **kwargs: Any) -> dict[str, Any]:
        errors: list[str] = []
        for provider in self.providers:
            try:
                return provider.fetch(symbol, **kwargs)
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                logger.warning("provider_failed", provider=provider.name, error=str(exc))
        raise DataProviderError("; ".join(errors))
