"""CryptoGhost v4 - AI Router híbrido (local + premium)."""

from dataclasses import dataclass
from enum import Enum

from backend.shared.ai_providers.base import AIResponse
from backend.shared.ai_providers.factory import get_ai_provider
from backend.shared.ai_providers.model_router import get_model_router
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_router")


class TaskComplexity(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    REASONING = "reasoning"
    MACRO = "macro"
    ANOMALY = "anomaly"
    INSTITUTIONAL = "institutional"


@dataclass
class RoutingDecision:
    provider: str
    model: str
    reason: str
    use_premium: bool


class HybridAIRouter:
    """Decide automaticamente entre IA local e premium."""

    PREMIUM_PROVIDERS = ["openai", "anthropic", "gemini"]

    TASK_ROUTING = {
        TaskComplexity.FAST: ("ollama", False),
        TaskComplexity.STANDARD: ("ollama", False),
        TaskComplexity.REASONING: ("openai", True),
        TaskComplexity.MACRO: ("anthropic", True),
        TaskComplexity.ANOMALY: ("openai", True),
        TaskComplexity.INSTITUTIONAL: ("anthropic", True),
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_router = get_model_router()
        self._premium_available = {
            "openai": bool(self.settings.openai_api_key),
            "anthropic": bool(self.settings.anthropic_api_key),
            "gemini": bool(self.settings.gemini_api_key),
        }

    def route(self, task: TaskComplexity, prefer_premium: bool = False) -> RoutingDecision:
        default_provider, wants_premium = self.TASK_ROUTING.get(task, ("ollama", False))
        use_premium = prefer_premium or wants_premium

        if use_premium:
            for provider in self.PREMIUM_PROVIDERS:
                if self._premium_available.get(provider):
                    model = {
                        "openai": self.settings.openai_model,
                        "anthropic": self.settings.anthropic_model,
                        "gemini": self.settings.gemini_model,
                    }[provider]
                    return RoutingDecision(provider, model, f"Premium para {task.value}", True)

        model = self._local_router.select_model()
        return RoutingDecision("ollama", model, f"Local para {task.value}", False)

    async def generate(
        self,
        prompt: str,
        task: TaskComplexity = TaskComplexity.STANDARD,
        system: str | None = None,
        prefer_premium: bool = False,
    ) -> AIResponse:
        decision = self.route(task, prefer_premium)
        prompt = self._local_router.sanitize_prompt(prompt)

        if decision.use_premium:
            try:
                provider = get_ai_provider(decision.provider)
                response = await provider.generate(prompt, system)
                response.metadata = {"router": decision.provider, "model": decision.model, "premium": True}
                return response
            except Exception as exc:
                logger.warning("premium_fallback_local", error=str(exc))

        response = await self._local_router.generate(prompt, system, model=decision.model)
        response.metadata = {"router": "ollama", "model": decision.model, "premium": False}
        return response

    async def explain_investment(self, decision_payload: dict, prefer_premium: bool = True) -> str:
        prompt = (
            f"Explique de forma institucional e clara esta recomendação de investimento:\n"
            f"{decision_payload}\n"
            f"Inclua: por que investir ou evitar, risco, probabilidade e fatores macro."
        )
        system = "Você é um analista quantitativo institucional. Responda em português, objetivo e baseado em dados."
        try:
            response = await self.generate(prompt, TaskComplexity.REASONING, system, prefer_premium)
            return response.content
        except Exception as exc:
            logger.warning("explain_investment_failed", error=str(exc))
            reasons = decision_payload.get("reasons", [])
            return " | ".join(reasons) if reasons else "Análise baseada em score quantitativo multi-fator."


_router: HybridAIRouter | None = None


def get_ai_router() -> HybridAIRouter:
    global _router
    if _router is None:
        _router = HybridAIRouter()
    return _router
