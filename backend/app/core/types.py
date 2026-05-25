"""CryptoGhost v6 — tipos compartilhados."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MarketRegimeV6(str, Enum):
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    NEWS_DRIVEN = "NEWS_DRIVEN"


class SignalClassification(str, Enum):
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    HOLD = "HOLD"
    BUY = "BUY"
    STRONG_BUY = "STRONG_BUY"


Classification = SignalClassification


@dataclass
class AgentVoteV3:
    agent: str
    signal: str
    confidence: float
    explanation: str = ""
    historical_accuracy: float = 0.5
    regime_accuracy: float = 0.5
    volatility_confidence: float = 0.5
    weight: float = 0.2
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass
class ConsensusResultV3:
    symbol: str
    final_decision: str
    final_score: float
    classification: SignalClassification
    consensus: float
    calibrated_confidence: float
    technical_score: float
    sentiment_score: float
    regime_alignment: float
    agreement: int
    disagreement: int
    conflicts: list[str]
    agent_votes: list[AgentVoteV3]
    can_execute: bool
    rejection_reasons: list[str] = field(default_factory=list)
    expires_at: datetime | None = None


@dataclass
class FeatureSnapshot:
    symbol: str
    timeframe: str
    timestamp: datetime
    features: dict[str, float]
    schema_version: str = "v6.0"


@dataclass
class TradeMemoryEntry:
    asset: str
    regime: str
    setup: str
    entry: float
    exit: float | None
    pnl: float
    duration_hours: float
    confidence: float
    consensus: float
    features_snapshot: dict[str, Any]
    result: str
    market_conditions: dict[str, Any]
