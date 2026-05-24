"""CryptoGhost - OpenAI Provider."""

import hashlib
import math

import httpx

from backend.shared.ai_providers.base import AIProvider, AIResponse
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_provider.openai")


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.embed_model = settings.openai_embed_model
        self.timeout = settings.ai_request_timeout

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": kwargs.get("model", self.model), "messages": messages},
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return AIResponse(
            content=choice,
            model=data.get("model", self.model),
            provider=self.name,
            tokens_used=usage.get("total_tokens", 0),
        )

    async def embed(self, text: str) -> list[float]:
        if not self.api_key:
            return self._fallback_embed(text)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.embed_model, "input": text},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def health_check(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _fallback_embed(text: str, dim: int = 384) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        values = [digest[i % len(digest)] / 255.0 for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
