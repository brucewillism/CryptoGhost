"""CryptoGhost v4 - Contexto compartilhado para priorização de investimentos."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class MarketContext:
    """Contexto unificado consumido por todos os engines de investimento."""

    symbol: str
    df: pd.DataFrame
    analysis: dict
    sentiment: dict
    risk: dict
    regime: dict
    consensus: dict
    explanation: dict
    macro: dict | None = None
    quant_v3: dict | None = None
    asset_class: str = "crypto"
    calibrated_confidence: float = 0.5
    liquidity_score: float = 0.5
    correlations: dict[str, float] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return float(self.analysis.get("score", 50))

    @property
    def volatility(self) -> float:
        return float(self.analysis.get("volatility", 50))

    @property
    def momentum(self) -> float:
        return float(self.analysis.get("momentum", 0))

    @property
    def regime_name(self) -> str:
        return str(self.regime.get("regime", "sideways"))

    @property
    def crash_probability(self) -> float:
        return float(self.risk.get("crash_probability", 0))

    @property
    def sentiment_score(self) -> float:
        return float(self.sentiment.get("score", 0.5))

    @property
    def decision(self) -> str:
        return str(self.consensus.get("final_decision", "HOLD"))
