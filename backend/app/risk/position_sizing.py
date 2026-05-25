"""PositionSizingService — tamanho por FINAL_SCORE."""

from decimal import Decimal, ROUND_DOWN

from backend.shared.config import get_settings


class PositionSizingService:
    """Sinais fracos = posições menores; sinais fortes = posições maiores."""

    TIERS = (
        (85, 0.10),
        (75, 0.08),
        (60, 0.06),
        (50, 0.03),
        (0, 0.0),
    )

    def __init__(self) -> None:
        self.settings = get_settings()

    def allocation_pct(self, final_score: float) -> float:
        for threshold, pct in self.TIERS:
            if final_score >= threshold:
                return min(pct * 100, self.settings.max_single_allocation_pct)
        return 0.0

    def compute_quantity(
        self,
        final_score: float,
        price: Decimal,
        portfolio_usdt: Decimal,
    ) -> tuple[Decimal, float]:
        alloc_pct = self.allocation_pct(final_score)
        if alloc_pct <= 0 or price <= 0:
            return Decimal("0"), alloc_pct

        investment = (portfolio_usdt * Decimal(str(alloc_pct)) / Decimal("100")).quantize(Decimal("0.01"))
        qty = (investment / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        return qty, alloc_pct
