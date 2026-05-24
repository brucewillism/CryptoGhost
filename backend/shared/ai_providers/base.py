"""CryptoGhost - AI Provider base interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstração para provedores de IA local (Ollama) e cloud."""

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> AIResponse:
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
