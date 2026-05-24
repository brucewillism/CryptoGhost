"""Quant platform schema v3."""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_quant"
down_revision: Union[str, None] = "002_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    ("rl_policies", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("algorithm", sa.String(20), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("checkpoint_path", sa.String(500), nullable=False),
        sa.Column("reward", sa.Float(), nullable=False),
        sa.Column("episode", sa.Integer(), default=0),
        sa.Column("metrics", postgresql.JSONB()),
        sa.Column("is_best", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_rl_policies_agent_created", ["agent_name", "created_at"]),
    ("feature_versions", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("feature_name", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(30)),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("ttl_seconds", sa.Integer()),
        sa.Column("validated", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_feature_versions_name_version", ["feature_name", "version"]),
    ("event_streams", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_id", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), default="processed"),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_event_streams_type_created", ["event_type", "created_at"]),
    ("scenario_embeddings", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("scenario_label", sa.String(100), nullable=False),
        sa.Column("embedding", postgresql.JSONB(), nullable=False),
        sa.Column("market_state", postgresql.JSONB(), nullable=False),
        sa.Column("outcome", sa.String(50)),
        sa.Column("outcome_pct", sa.Float()),
        sa.Column("similarity_reference", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_scenario_embeddings_symbol_created", ["symbol", "created_at"]),
    ("calibrated_predictions", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("agent", sa.String(50), nullable=False),
        sa.Column("raw_confidence", sa.Float(), nullable=False),
        sa.Column("calibrated_confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_calibrated_predictions_symbol_created", ["symbol", "created_at"]),
    ("temporal_memory", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("memory_type", sa.String(20), nullable=False),
        sa.Column("context", postgresql.JSONB(), nullable=False),
        sa.Column("embedding", postgresql.JSONB()),
        sa.Column("decision", sa.String(20)),
        sa.Column("outcome", sa.String(50)),
        sa.Column("outcome_pct", sa.Float()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_temporal_memory_agent_created", ["agent_name", "created_at"]),
    ("ensemble_decisions", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("final_decision", sa.String(20), nullable=False),
        sa.Column("meta_confidence", sa.Float(), nullable=False),
        sa.Column("stacking_weights", postgresql.JSONB(), nullable=False),
        sa.Column("agent_predictions", postgresql.JSONB(), nullable=False),
        sa.Column("regime", sa.String(30)),
        sa.Column("method", sa.String(30), default="stacking"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_ensemble_decisions_symbol_created", ["symbol", "created_at"]),
    ("simulation_results", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("simulation_type", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("pnl", sa.Numeric(20, 8)),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_simulation_results_created", ["created_at"]),
    ("drift_reports", [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("drift_score", sa.Float(), nullable=False),
        sa.Column("accuracy_current", sa.Float(), nullable=False),
        sa.Column("accuracy_baseline", sa.Float(), nullable=False),
        sa.Column("false_positive_rate", sa.Float()),
        sa.Column("retrain_recommended", sa.Boolean(), default=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ], "ix_drift_reports_agent_created", ["agent_name", "created_at"]),
]


def upgrade() -> None:
    for name, cols, idx_name, idx_cols in TABLES:
        op.create_table(name, *cols)
        op.create_index(idx_name, name, idx_cols)


def downgrade() -> None:
    for name, _, _, _ in reversed(TABLES):
        op.drop_table(name)
