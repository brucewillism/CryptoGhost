"""CryptoGhost - Modelos de Inteligência Artificial."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base


class AIDecision(Base):
    __tablename__ = "ai_decisions"
    __table_args__ = (Index("ix_ai_decisions_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    context: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIExplanation(Base):
    __tablename__ = "ai_explanations"
    __table_args__ = (Index("ix_ai_explanations_decision_id", "decision_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[list | None] = mapped_column(JSONB)
    feature_importance: Mapped[dict | None] = mapped_column(JSONB)
    shap_values: Mapped[dict | None] = mapped_column(JSONB)
    decision_trace: Mapped[list | None] = mapped_column(JSONB)
    textual_explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SentimentHistory(Base):
    __tablename__ = "sentiment_history"
    __table_args__ = (Index("ix_sentiment_history_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str | None] = mapped_column(String(30))
    market_sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSONB)
    bullish_pct: Mapped[float | None] = mapped_column(Float)
    bearish_pct: Mapped[float | None] = mapped_column(Float)
    panic_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    euphoria_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketRegimeRecord(Base):
    __tablename__ = "market_regimes"
    __table_args__ = (Index("ix_market_regimes_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    regime: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    volatility: Mapped[float | None] = mapped_column(Float)
    trend_strength: Mapped[float | None] = mapped_column(Float)
    features: Mapped[dict | None] = mapped_column(JSONB)
    strategy_adjustment: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PortfolioAnalysisRecord(Base):
    __tablename__ = "portfolio_analysis"
    __table_args__ = (Index("ix_portfolio_analysis_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    sortino_ratio: Mapped[float | None] = mapped_column(Float)
    var_95: Mapped[float | None] = mapped_column(Float)
    max_concentration: Mapped[float | None] = mapped_column(Float)
    correlation_matrix: Mapped[dict | None] = mapped_column(JSONB)
    exposure_by_asset: Mapped[dict | None] = mapped_column(JSONB)
    recommendations: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsAnalysisRecord(Base):
    __tablename__ = "news_analysis"
    __table_args__ = (Index("ix_news_analysis_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    impact: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    categories: Mapped[list | None] = mapped_column(JSONB)
    url: Mapped[str | None] = mapped_column(String(1000))
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIConsensusRecord(Base):
    __tablename__ = "ai_consensus"
    __table_args__ = (Index("ix_ai_consensus_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    final_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    agreement: Mapped[int] = mapped_column(Integer, nullable=False)
    disagreement: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_votes: Mapped[dict | None] = mapped_column(JSONB)
    conflicts: Mapped[list | None] = mapped_column(JSONB)
    explanation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MacroIndicatorRecord(Base):
    __tablename__ = "macro_indicators"
    __table_args__ = (Index("ix_macro_indicators_name_created", "indicator_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    change_pct: Mapped[float | None] = mapped_column(Float)
    impact: Mapped[str | None] = mapped_column(String(20))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIMemoryRecord(Base):
    __tablename__ = "ai_memory"
    __table_args__ = (Index("ix_ai_memory_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(20))
    performance_pct: Mapped[float | None] = mapped_column(Float)
    market_context: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list | None] = mapped_column(JSONB)
    was_correct: Mapped[bool | None] = mapped_column(Boolean)
    lesson: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetAnalysisRecord(Base):
    __tablename__ = "asset_analysis"
    __table_args__ = (Index("ix_asset_analysis_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    trend: Mapped[str] = mapped_column(String(20), nullable=False)
    risk: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(30), nullable=False)
    indicators: Mapped[dict | None] = mapped_column(JSONB)
    strength_score: Mapped[float | None] = mapped_column(Float)
    reversal_probability: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
