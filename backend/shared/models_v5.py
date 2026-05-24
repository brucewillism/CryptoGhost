"""CryptoGhost v5 - Modelos self-improving quant."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base


class MetaLearningRecord(Base):
    __tablename__ = "meta_learning_records"
    __table_args__ = (Index("ix_meta_learning_regime_created", "market_regime", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    market_regime: Mapped[str] = mapped_column(String(30), nullable=False)
    historical_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PredictionValidationRecord(Base):
    __tablename__ = "prediction_validations"
    __table_args__ = (Index("ix_prediction_validations_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    predicted_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    actual_return_pct: Mapped[float | None] = mapped_column(Float)
    predicted_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    calibration_error: Mapped[float | None] = mapped_column(Float)
    direction_correct: Mapped[bool | None] = mapped_column(Boolean)
    validation_score: Mapped[float] = mapped_column(Float, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, default=7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyEvolutionRecord(Base):
    __tablename__ = "strategy_evolutions"
    __table_args__ = (Index("ix_strategy_evolutions_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    fitness_score: Mapped[float] = mapped_column(Float, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DriftDetectionRecord(Base):
    __tablename__ = "drift_detection_v5"
    __table_args__ = (Index("ix_drift_detection_v5_model_created", "model_name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    drift_type: Mapped[str] = mapped_column(String(30), nullable=False)
    drift_score: Mapped[float] = mapped_column(Float, nullable=False)
    regime_shift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    retrain_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RealPerformanceRecord(Base):
    __tablename__ = "real_performance_metrics"
    __table_args__ = (Index("ix_real_performance_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[str] = mapped_column(String(50), default="default")
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    sortino_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cagr_pct: Mapped[float] = mapped_column(Float, nullable=False)
    hit_rate: Mapped[float] = mapped_column(Float, nullable=False)
    expected_vs_actual_pct: Mapped[float] = mapped_column(Float, nullable=False)
    alpha_pct: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AITruthRecord(Base):
    __tablename__ = "ai_truth_scores"
    __table_args__ = (Index("ix_ai_truth_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    truth_score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    corrected_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    overconfidence_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    hallucination_risk: Mapped[float] = mapped_column(Float, default=0.0)
    validation_basis: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SelfImprovementRecord(Base):
    __tablename__ = "self_improvement_logs"
    __table_args__ = (Index("ix_self_improvement_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(80), nullable=False)
    before_value: Mapped[float | None] = mapped_column(Float)
    after_value: Mapped[float | None] = mapped_column(Float)
    improvement_pct: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketStateRecord(Base):
    __tablename__ = "market_state_intelligence"
    __table_args__ = (Index("ix_market_state_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    structural_state: Mapped[str] = mapped_column(String(50), nullable=False)
    fragility_score: Mapped[float] = mapped_column(Float, nullable=False)
    hidden_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    trend_exhaustion: Mapped[float] = mapped_column(Float, nullable=False)
    manipulation_score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderflowSnapshotRecord(Base):
    __tablename__ = "orderflow_snapshots"
    __table_args__ = (Index("ix_orderflow_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    cumulative_delta: Mapped[float] = mapped_column(Float, nullable=False)
    delta_imbalance: Mapped[float] = mapped_column(Float, nullable=False)
    absorption_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    spoofing_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    smart_money_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    footprint: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
