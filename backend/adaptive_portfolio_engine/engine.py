"""CryptoGhost v4 - Adaptive Portfolio Engine."""

from dataclasses import dataclass

from backend.capital_allocator.engine import CapitalAllocation
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.adaptive_portfolio_engine")


@dataclass
class PortfolioAdaptation:
    regime: str
    previous_allocations: dict[str, float]
    adjusted_allocations: dict[str, float]
    defensive_mode: bool
    rebalance_required: bool
    actions: list[str]


class AdaptivePortfolioEngine:
    """Adapta carteira conforme regime e volatilidade."""

    DEFENSIVE_ASSETS = {"Cash", "GOLD", "USDT", "BOND"}

    def adapt(
        self,
        allocation: CapitalAllocation,
        regime: str,
        volatility: float,
        crash_probability: float,
    ) -> PortfolioAdaptation:
        prev = dict(allocation.allocations)
        adjusted = dict(prev)
        actions: list[str] = []
        defensive = regime in ("bear_market", "high_volatility") or crash_probability > 0.5

        if defensive:
            cash_target = max(40, allocation.cash_pct + 15)
            scale = (100 - cash_target) / max(sum(v for k, v in adjusted.items() if k != "Cash"), 1)
            for k in list(adjusted.keys()):
                if k != "Cash":
                    adjusted[k] = round(adjusted[k] * scale, 1)
            adjusted["Cash"] = round(cash_target, 1)
            actions.append("Aumentar caixa em regime defensivo")

        if volatility > 80:
            for k in list(adjusted.keys()):
                if k != "Cash":
                    adjusted[k] = round(adjusted[k] * 0.7, 1)
            adjusted["Cash"] = round(100 - sum(v for k, v in adjusted.items() if k != "Cash"), 1)
            actions.append("Reduzir exposição por volatilidade extrema")

        if crash_probability > 0.6:
            adjusted = {"Cash": 70.0}
            for k in prev:
                if k != "Cash" and k in adjusted:
                    del adjusted[k]
            actions.append("Proteção emergencial — crash probability elevada")

        total = sum(adjusted.values())
        if abs(total - 100) > 0.5:
            adjusted["Cash"] = round(adjusted.get("Cash", 0) + (100 - total), 1)

        rebalance = any(abs(prev.get(k, 0) - adjusted.get(k, 0)) > 5 for k in set(prev) | set(adjusted))

        return PortfolioAdaptation(
            regime=regime, previous_allocations=prev, adjusted_allocations=adjusted,
            defensive_mode=defensive, rebalance_required=rebalance, actions=actions,
        )
