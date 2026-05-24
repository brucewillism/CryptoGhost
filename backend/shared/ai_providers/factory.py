"""CryptoGhost - AI Provider Factory."""

from backend.shared.ai_providers.base import AIProvider
from backend.shared.ai_providers.claude_provider import ClaudeProvider
from backend.shared.ai_providers.gemini_provider import GeminiProvider
from backend.shared.ai_providers.ollama_provider import OllamaProvider
from backend.shared.ai_providers.openai_provider import OpenAIProvider
from backend.shared.config import get_settings

_PROVIDERS: dict[str, type[AIProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
}


def get_ai_provider(provider: str | None = None) -> AIProvider:
    settings = get_settings()
    name = (provider or settings.ai_provider_default).lower()
    if name not in _PROVIDERS:
        raise ValueError(f"Provider '{name}' não suportado. Opções: {list(_PROVIDERS)}")
    return _PROVIDERS[name]()
