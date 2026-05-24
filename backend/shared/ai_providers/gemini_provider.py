"""CryptoGhost - Google Gemini Provider."""

import hashlib
import math

import httpx

from backend.shared.ai_providers.base import AIProvider, AIResponse
from backend.shared.config import get_settings


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.timeout = settings.ai_request_timeout

    async def generate(self, prompt: str, system: str | None = None, **kwargs) -> AIResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada")

        model = kwargs.get("model", self.model)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": self.api_key},
                json={"contents": [{"parts": [{"text": full_prompt}]}]},
            )
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return AIResponse(content=content, model=model, provider=self.name)

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
