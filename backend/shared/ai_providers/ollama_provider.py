"""CryptoGhost - Ollama AI Provider (Llama, DeepSeek, Mistral)."""

import hashlib
import math
import time

import httpx

from backend.shared.ai_providers.base import AIProvider, AIResponse
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.startup_log import ollama as ollama_log

logger = get_logger("cryptoghost.ai_provider.ollama")


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.effective_ollama_base_url
        self.model = settings.effective_ollama_model
        self.secondary_model = settings.effective_ollama_model_secondary
        self.embed_model = settings.effective_ollama_embed_model
        self.timeout = settings.effective_ollama_timeout
        self.retry_max = max(1, settings.ollama_retry_max)
        self.retry_backoff = max(0.5, settings.ollama_retry_backoff)
        self._model_cache: list[str] | None = None

    async def _fetch_models(self) -> list[str]:
        if self._model_cache is not None:
            return self._model_cache
        try:
            response = await self._request_with_retry("GET", f"{self.base_url}/api/tags")
            data = response.json()
            self._model_cache = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            self._model_cache = []
        return self._model_cache

    async def _resolve_model(self, model: str) -> str:
        available = await self._fetch_models()
        if not available:
            return model
        if model in available:
            return model
        for name in available:
            base = name.split(":")[0]
            if name.startswith(model) or model.startswith(base) or base.startswith(model.split(":")[0]):
                return name
        return available[0]

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self.retry_max + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_exc = exc
                wait = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "ollama_retry",
                    attempt=attempt,
                    max_attempts=self.retry_max,
                    wait_s=wait,
                    error=str(exc),
                )
                if attempt < self.retry_max:
                    import asyncio

                    await asyncio.sleep(wait)
        raise last_exc or RuntimeError("Ollama request failed")

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        models_to_try = []
        primary = kwargs.get("model", self.model)
        primary = await self._resolve_model(primary)
        models_to_try.append(primary)
        if self.secondary_model and self.secondary_model not in models_to_try:
            models_to_try.append(await self._resolve_model(self.secondary_model))

        last_error: Exception | None = None
        for model_name in models_to_try:
            payload: dict = {"model": model_name, "prompt": prompt, "stream": False}
            if system:
                payload["system"] = system
            try:
                start = time.perf_counter()
                response = await self._request_with_retry(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                data = response.json()
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                used_fallback = model_name != primary
                if used_fallback:
                    ollama_log("fallback_model_used", primary=primary, fallback=model_name)
                return AIResponse(
                    content=data.get("response", ""),
                    model=data.get("model", model_name),
                    provider=self.name,
                    tokens_used=data.get("eval_count", 0),
                    metadata={"latency_ms": latency_ms, "fallback": used_fallback},
                )
            except Exception as exc:
                last_error = exc
                logger.warning("ollama_generate_failed", model=model_name, error=str(exc))

        raise RuntimeError(f"Ollama generate falhou após fallback: {last_error}")

    async def embed(self, text: str) -> list[float]:
        try:
            response = await self._request_with_retry(
                "POST",
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            data = response.json()
            return data.get("embedding", self._fallback_embed(text))
        except Exception as exc:
            logger.warning("ollama_embed_failed", error=str(exc))
            return self._fallback_embed(text)

    async def health_check(self) -> bool:
        try:
            response = await self._request_with_retry("GET", f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as exc:
            logger.warning("ollama_health_failed", error=str(exc))
            return False

    @staticmethod
    def _fallback_embed(text: str, dim: int = 384) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        values = [digest[i % len(digest)] / 255.0 for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
