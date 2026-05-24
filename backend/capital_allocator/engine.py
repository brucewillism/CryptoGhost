"""CryptoGhost v4 - Capital Allocator."""

from dataclasses import dataclass

from backend.investment.context import MarketContext
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.capital_allocator")


@dataclass
class AllocationItem:
    symbol: str
    allocation_pct: float
    confidence: float
    expected_return_pct: float


@dataclass
class CapitalAllocation:
    allocations: dict[str, float]
    items: list[AllocationItem]
    total_exposure_pct: float
    cash_pct: float
    rationale: str


class CapitalAllocator:
    """Alocação dinâmica baseada em score, confiança e regime."""

    MAX_TOTAL_EXPOSURE = 70.0
    MIN_CASH = 20.0
    MAX_SINGLE_ASSET = 35.0

    def allocate(
        self,
        ranked: list[dict],
        regime: str = "sideways",
    ) -> CapitalAllocation:
        settings = get_settings()
        max_exp = min(float(settings.max_exposure_pct), self.MAX_TOTAL_EXPOSURE)

        regime_exp = {"bull_market": max_exp, "bear_market": max_exp * 0.4, "high_volatility": max_exp * 0.25, "sideways": max_exp * 0.6}.get(regime, max_exp * 0.5)

        approved = [r for r in ranked if r.get("approved", False) and r.get("priority_score", 0) >= 50]
        if not approved:
            cash = 100.0
            return CapitalAllocation(allocations={"Cash": cash}, items=[], total_exposure_pct=0, cash_pct=cash, rationale="Nenhuma oportunidade aprovada — capital protegido")

        weights = []
        for r in approved:
            w = r["priority_score"] * r.get("confidence", 0.5) * r.get("profit_probability", 0.5)
            weights.append(max(0, w))

        total_w = sum(weights) or 1
        items: list[AllocationItem] = []
        allocations: dict[str, float] = {}
        used = 0.0

        for r, w in zip(approved, weights):
            pct = (w / total_w) * regime_exp
            pct = min(self.MAX_SINGLE_ASSET, pct)
            sym = r["symbol"].split("/")[0]
            allocations[sym] = round(pct, 1)
            used += pct
            items.append(AllocationItem(
                symbol=r["symbol"], allocation_pct=round(pct, 1),
                confidence=r.get("confidence", 0), expected_return_pct=r.get("expected_return", 0),
            ))

        cash = max(self.MIN_CASH, 100 - used)
        if used + cash > 100:
            scale = (100 - cash) / used
            allocations = {k: round(v * scale, 1) for k, v in allocations.items()}
            used = sum(allocations.values())

        allocations["Cash"] = round(cash, 1)

        return CapitalAllocation(
            allocations=allocations, items=items,
            total_exposure_pct=round(used, 1), cash_pct=round(cash, 1),
            rationale=f"Regime {regime}, {len(approved)} oportunidades aprovadas, exposição máx {regime_exp:.0f}%",
        )
