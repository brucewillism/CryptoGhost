"""CryptoGhost - Anthropic Claude Provider."""

import hashlib
import math

import httpx

from backend.shared.ai_providers.base import AIProvider, AIResponse
from backend.shared.config import get_settings


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.timeout = settings.ai_request_timeout

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada")

        payload: dict = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        return AIResponse(
            content=content,
            model=data.get("model", self.model),
            provider=self.name,
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    async def embed(self, text: str) -> list[float]:
        return self._fallback_embed(text)

    async def health_check(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _fallback_embed(text: str, dim: int = 384) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        values = [digest[i % len(digest)] / 255.0 for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
