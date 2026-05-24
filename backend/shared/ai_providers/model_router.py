"""CryptoGhost v3 - Model Router com fallback e load balancing."""

import random
from dataclasses import dataclass

import httpx

from backend.shared.ai_providers.base import AIProvider, AIResponse
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.model_router")

SUPPORTED_OLLAMA_MODELS = ["llama3", "deepseek-r1", "mistral", "qwen2.5", "phi3"]


@dataclass
class ModelHealth:
    model: str
    provider: str
    healthy: bool
    latency_ms: float = 0


class ModelRouter:
    """Roteador de modelos com fallback, load balancing e anti-injection."""

    INJECTION_PATTERNS = ["ignore previous", "system prompt", "jailbreak", "override instructions"]

    def __init__(self) -> None:
        self.settings = get_settings()
        self._models = self.settings.ollama_models_list if hasattr(self.settings, "ollama_models_list") else SUPPORTED_OLLAMA_MODELS
        self._health: dict[str, ModelHealth] = {}
        self._request_counts: dict[str, int] = {}

    def sanitize_prompt(self, prompt: str) -> str:
        lower = prompt.lower()
        for pattern in self.INJECTION_PATTERNS:
            if pattern in lower:
                logger.warning("prompt_injection_blocked", pattern=pattern)
                raise ValueError("Prompt rejeitado por segurança (possível injection)")
        return prompt[:8000]

    async def check_health(self, model: str) -> ModelHealth:
        import time
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.settings.effective_ollama_base_url}/api/tags")
                healthy = r.status_code == 200
        except Exception:
            healthy = False

        latency = (time.perf_counter() - start) * 1000
        health = ModelHealth(model=model, provider="ollama", healthy=healthy, latency_ms=latency)
        self._health[model] = health
        return health

    def select_model(self, preferred: str | None = None) -> str:
        if preferred and preferred in self._models:
            return preferred

        healthy = [m for m, h in self._health.items() if h.healthy]
        if healthy:
            return min(healthy, key=lambda m: self._request_counts.get(m, 0))

        return random.choice(self._models)

    async def generate(self, prompt: str, system: str | None = None, model: str | None = None) -> AIResponse:
        from backend.shared.ai_providers.ollama_provider import OllamaProvider

        prompt = self.sanitize_prompt(prompt)
        selected = self.select_model(model)
        self._request_counts[selected] = self._request_counts.get(selected, 0) + 1

        for attempt_model in [selected] + [m for m in self._models if m != selected]:
            try:
                provider = OllamaProvider()
                provider.model = attempt_model
                response = await provider.generate(prompt, system, model=attempt_model)
                response.metadata = {"routed_model": attempt_model, "fallback": attempt_model != selected}
                return response
            except Exception as exc:
                logger.warning("model_fallback", model=attempt_model, error=str(exc))
                self._health[attempt_model] = ModelHealth(attempt_model, "ollama", False)

        raise RuntimeError("Todos os modelos falharam")


_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
