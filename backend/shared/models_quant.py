"""CryptoGhost v3 - Modelos quantitativos institucionais."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base


class RLPolicyRecord(Base):
    __tablename__ = "rl_policies"
    __table_args__ = (Index("ix_rl_policies_agent_created", "agent_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    checkpoint_path: Mapped[str] = mapped_column(String(500), nullable=False)
    reward: Mapped[float] = mapped_column(Float, nullable=False)
    episode: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict | None] = mapped_column(JSONB)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureVersionRecord(Base):
    __tablename__ = "feature_versions"
    __table_args__ = (Index("ix_feature_versions_name_version", "feature_name", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(30))
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    ttl_seconds: Mapped[int | None] = mapped_column(Integer)
    validated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventStreamRecord(Base):
    __tablename__ = "event_streams"
    __table_args__ = (Index("ix_event_streams_type_created", "event_type", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScenarioEmbeddingRecord(Base):
    __tablename__ = "scenario_embeddings"
    __table_args__ = (Index("ix_scenario_embeddings_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    scenario_label: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding: Mapped[list] = mapped_column(JSONB, nullable=False)
    market_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(50))
    outcome_pct: Mapped[float | None] = mapped_column(Float)
    similarity_reference: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CalibratedPredictionRecord(Base):
    __tablename__ = "calibrated_predictions"
    __table_args__ = (Index("ix_calibrated_predictions_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TemporalMemoryRecord(Base):
    __tablename__ = "temporal_memory"
    __table_args__ = (Index("ix_temporal_memory_agent_created", "agent_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSONB)
    decision: Mapped[str | None] = mapped_column(String(20))
    outcome: Mapped[str | None] = mapped_column(String(50))
    outcome_pct: Mapped[float | None] = mapped_column(Float)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EnsembleDecisionRecord(Base):
    __tablename__ = "ensemble_decisions"
    __table_args__ = (Index("ix_ensemble_decisions_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    final_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    meta_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    stacking_weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    agent_predictions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    regime: Mapped[str | None] = mapped_column(String(30))
    method: Mapped[str] = mapped_column(String(30), default="stacking")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SimulationResultRecord(Base):
    __tablename__ = "simulation_results"
    __table_args__ = (Index("ix_simulation_results_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DriftReportRecord(Base):
    __tablename__ = "drift_reports"
    __table_args__ = (Index("ix_drift_reports_agent_created", "agent_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_current: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_baseline: Mapped[float] = mapped_column(Float, nullable=False)
    false_positive_rate: Mapped[float | None] = mapped_column(Float)
    retrain_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
