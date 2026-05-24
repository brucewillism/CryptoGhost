"""CryptoGhost v5 - Portfolio Survival Engine."""

from dataclasses import dataclass

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.portfolio_survival")


@dataclass
class SurvivalAssessment:
    survival_score: float
    mode: str
    recommended_cash_pct: float
    exposure_multiplier: float
    emergency_deleverage: bool
    black_swan_protection: bool
    actions: list[str]


class PortfolioSurvivalEngine:
    """Preservação de capital acima de tudo."""

    MODES = ("normal", "defensive", "survival", "emergency")

    def assess(
        self,
        crash_probability: float,
        volatility: float,
        drawdown_pct: float,
        systemic_risk: float = 0.0,
    ) -> SurvivalAssessment:
        settings = get_settings()
        actions: list[str] = []
        score = 100.0

        score -= crash_probability * 40
        score -= max(0, volatility - 50) * 0.5
        score -= drawdown_pct * 2
        score -= systemic_risk * 30
        score = max(0, min(100, score))

        if score < 25 or crash_probability > 0.7:
            mode = "emergency"
            cash = 80.0
            mult = 0.1
            emergency = True
            black_swan = crash_probability > 0.6
            actions.extend(["Modo emergência", "Deleveraging imediato", "Caixa mínimo 80%"])
        elif score < 45 or volatility > 75:
            mode = "survival"
            cash = max(settings.min_cash_allocation_pct, 50)
            mult = 0.3
            emergency = drawdown_pct > 15
            black_swan = False
            actions.extend(["Modo sobrevivência", "Reduzir exposição 70%"])
        elif score < 65 or crash_probability > 0.4:
            mode = "defensive"
            cash = max(settings.min_cash_allocation_pct, 35)
            mult = 0.6
            emergency = False
            black_swan = False
            actions.append("Modo defensivo — aumentar caixa")
        else:
            mode = "normal"
            cash = settings.min_cash_allocation_pct
            mult = 1.0
            emergency = False
            black_swan = False

        return SurvivalAssessment(
            survival_score=round(score, 2), mode=mode, recommended_cash_pct=round(cash, 1),
            exposure_multiplier=round(mult, 2), emergency_deleverage=emergency,
            black_swan_protection=black_swan, actions=actions,
        )
