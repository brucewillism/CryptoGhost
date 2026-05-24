"""CryptoGhost v5 - Contexto self-improving."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class SelfImprovingContext:
    symbol: str
    df: pd.DataFrame
    regime: str
    v2_result: dict
    quant_v3: dict | None = None
    investment_v4: dict | None = None
    premium_data: dict = field(default_factory=dict)

    @property
    def expected_return(self) -> float:
        inv = self.investment_v4 or {}
        return float(inv.get("priority", {}).get("expected_return", 0))

    @property
    def confidence(self) -> float:
        inv = self.investment_v4 or {}
        return float(inv.get("priority", {}).get("confidence", 0.5))

    @property
    def crash_probability(self) -> float:
        return float(self.v2_result.get("risk", {}).get("crash_probability", 0))

    @property
    def volatility(self) -> float:
        return float(self.v2_result.get("analysis", {}).get("volatility", 50))

    @property
    def decision(self) -> str:
        return str(self.v2_result.get("consensus", {}).get("final_decision", "HOLD"))
