"""CryptoGhost v6 — Modelos quantitativos."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base

FEATURE_SCHEMA_VERSION = "v6.0"


class FeatureSnapshotRecord(Base):
    __tablename__ = "feature_snapshots"
    __table_args__ = (
        Index("ix_feature_snapshots_symbol_tf_ts", "symbol", "timeframe", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), default="1h")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), default=FEATURE_SCHEMA_VERSION)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketSignalV6Record(Base):
    __tablename__ = "market_signals_v6"
    __table_args__ = (Index("ix_market_signals_v6_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(20), nullable=False)
    final_decision: Mapped[str] = mapped_column(String(10), nullable=False)
    consensus: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    regime_alignment: Mapped[float] = mapped_column(Float, default=0.0)
    agreement: Mapped[int] = mapped_column(Integer, default=0)
    disagreement: Mapped[int] = mapped_column(Integer, default=0)
    conflicts: Mapped[list | None] = mapped_column(JSONB)
    agent_votes: Mapped[list | None] = mapped_column(JSONB)
    can_execute: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reasons: Mapped[list | None] = mapped_column(JSONB)
    regime: Mapped[str | None] = mapped_column(String(30))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentPerformanceRecord(Base):
    __tablename__ = "agent_performance"
    __table_args__ = (
        Index("ix_agent_performance_agent_regime", "agent_name", "regime", "symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), default="*")
    timeframe: Mapped[str] = mapped_column(String(10), default="1h")
    regime: Mapped[str] = mapped_column(String(30), default="*")
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    dynamic_weight: Mapped[float] = mapped_column(Float, default=0.2)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TradeMemoryRecord(Base):
    __tablename__ = "trade_memory"
    __table_args__ = (Index("ix_trade_memory_asset_created", "asset", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset: Mapped[str] = mapped_column(String(30), nullable=False)
    regime: Mapped[str] = mapped_column(String(30), nullable=False)
    setup: Mapped[str] = mapped_column(String(50), default="unknown")
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    duration_hours: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    consensus: Mapped[float] = mapped_column(Float, nullable=False)
    features_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[str] = mapped_column(String(20), default="open")
    market_conditions: Mapped[dict | None] = mapped_column(JSONB)
    order_id: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TradeMemoryEmbeddingRecord(Base):
    __tablename__ = "trade_memory_embeddings"
    __table_args__ = (Index("ix_trade_memory_emb_trade", "trade_memory_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_memory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSONB)
    label: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacktestRunRecord(Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (Index("ix_backtest_runs_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbols: Mapped[list] = mapped_column(JSONB, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacktestTradeRecord(Base):
    __tablename__ = "backtest_trades"
    __table_args__ = (Index("ix_backtest_trades_run", "run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    slippage: Mapped[float] = mapped_column(Float, default=0.0)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PortfolioSnapshotRecord(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (Index("ix_portfolio_snapshots_created", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[str] = mapped_column(String(50), default="paper")
    total_value_usdt: Mapped[float] = mapped_column(Float, nullable=False)
    exposure_pct: Mapped[float] = mapped_column(Float, default=0.0)
    heat_score: Mapped[float] = mapped_column(Float, default=0.0)
    open_positions: Mapped[int] = mapped_column(Integer, default=0)
    daily_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RegimeHistoryV6Record(Base):
    __tablename__ = "regime_history_v6"
    __table_args__ = (Index("ix_regime_history_v6_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    regime: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    policy_applied: Mapped[dict | None] = mapped_column(JSONB)
    features: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SentimentV2Record(Base):
    __tablename__ = "sentiment_v2_history"
    __table_args__ = (Index("ix_sentiment_v2_symbol_created", "symbol", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSONB)
    news_impact: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(30), default="lexical")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
