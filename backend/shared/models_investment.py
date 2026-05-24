"""CryptoGhost v4 - Modelos de priorização inteligente de investimentos."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base


class InvestmentRankingRecord(Base):
    __tablename__ = "investment_rankings"
    __table_args__ = (Index("ix_investment_rankings_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(20), default="crypto")
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(40), nullable=False)
    reasons: Mapped[list | None] = mapped_column(JSONB)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OpportunityScoreRecord(Base):
    __tablename__ = "opportunity_scores"
    __table_args__ = (Index("ix_opportunity_scores_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExpectedReturnRecord(Base):
    __tablename__ = "expected_returns"
    __table_args__ = (Index("ix_expected_returns_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    drawdown_probable_pct: Mapped[float] = mapped_column(Float, nullable=False)
    upside_downside_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=14)
    confidence_interval: Mapped[dict] = mapped_column(JSONB, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InstitutionalSignalRecord(Base):
    __tablename__ = "institutional_signals"
    __table_args__ = (Index("ix_institutional_signals_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProbabilisticPredictionRecord(Base):
    __tablename__ = "probabilistic_predictions"
    __table_args__ = (Index("ix_probabilistic_predictions_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    bullish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    bearish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    sideways_probability: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdaptiveAllocationRecord(Base):
    __tablename__ = "adaptive_allocations"
    __table_args__ = (Index("ix_adaptive_allocations_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[str] = mapped_column(String(50), default="default")
    allocations: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_exposure_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cash_pct: Mapped[float] = mapped_column(Float, nullable=False)
    regime: Mapped[str | None] = mapped_column(String(30))
    rationale: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlphaDetectionRecord(Base):
    __tablename__ = "alpha_detections"
    __table_args__ = (Index("ix_alpha_detections_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    alpha_score: Mapped[float] = mapped_column(Float, nullable=False)
    alpha_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_edge_pct: Mapped[float] = mapped_column(Float, nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), default="moderate")
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
