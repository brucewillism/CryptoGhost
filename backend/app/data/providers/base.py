"""Interface base para data providers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, symbol: str, **kwargs: Any) -> dict[str, Any]:
        ...
