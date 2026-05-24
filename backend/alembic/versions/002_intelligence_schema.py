"""Intelligence platform schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_intelligence"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    tables = [
        ("ai_decisions", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("decision", sa.String(20), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("agent", sa.String(50), nullable=False),
            sa.Column("score", sa.Float()),
            sa.Column("context", postgresql.JSONB()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_ai_decisions_symbol_created", ["symbol", "created_at"]),
        ("ai_explanations", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("decision", sa.String(20), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("reasons", postgresql.JSONB()),
            sa.Column("feature_importance", postgresql.JSONB()),
            sa.Column("shap_values", postgresql.JSONB()),
            sa.Column("decision_trace", postgresql.JSONB()),
            sa.Column("textual_explanation", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_ai_explanations_decision_id", ["decision_id"]),
        ("sentiment_history", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30)),
            sa.Column("market_sentiment", sa.String(20), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("sources", postgresql.JSONB()),
            sa.Column("bullish_pct", sa.Float()),
            sa.Column("bearish_pct", sa.Float()),
            sa.Column("panic_detected", sa.Boolean(), default=False),
            sa.Column("euphoria_detected", sa.Boolean(), default=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_sentiment_history_created", ["created_at"]),
        ("market_regimes", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("regime", sa.String(30), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("volatility", sa.Float()),
            sa.Column("trend_strength", sa.Float()),
            sa.Column("features", postgresql.JSONB()),
            sa.Column("strategy_adjustment", sa.String(100)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_market_regimes_symbol_created", ["symbol", "created_at"]),
        ("portfolio_analysis", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("total_value", sa.Numeric(20, 8), nullable=False),
            sa.Column("sharpe_ratio", sa.Float()),
            sa.Column("sortino_ratio", sa.Float()),
            sa.Column("var_95", sa.Float()),
            sa.Column("max_concentration", sa.Float()),
            sa.Column("correlation_matrix", postgresql.JSONB()),
            sa.Column("exposure_by_asset", postgresql.JSONB()),
            sa.Column("recommendations", postgresql.JSONB()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_portfolio_analysis_created", ["created_at"]),
        ("news_analysis", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("source", sa.String(100), nullable=False),
            sa.Column("impact", sa.String(20), nullable=False),
            sa.Column("direction", sa.String(20), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("categories", postgresql.JSONB()),
            sa.Column("url", sa.String(1000)),
            sa.Column("summary", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_news_analysis_created", ["created_at"]),
        ("ai_consensus", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("final_decision", sa.String(20), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("agreement", sa.Integer(), nullable=False),
            sa.Column("disagreement", sa.Integer(), nullable=False),
            sa.Column("agent_votes", postgresql.JSONB()),
            sa.Column("conflicts", postgresql.JSONB()),
            sa.Column("explanation_id", postgresql.UUID(as_uuid=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_ai_consensus_symbol_created", ["symbol", "created_at"]),
        ("macro_indicators", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("indicator_name", sa.String(50), nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.Column("change_pct", sa.Float()),
            sa.Column("impact", sa.String(20)),
            sa.Column("metadata", postgresql.JSONB()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_macro_indicators_name_created", ["indicator_name", "created_at"]),
        ("ai_memory", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("decision", sa.String(20), nullable=False),
            sa.Column("outcome", sa.String(20)),
            sa.Column("performance_pct", sa.Float()),
            sa.Column("market_context", postgresql.JSONB()),
            sa.Column("embedding", postgresql.JSONB()),
            sa.Column("was_correct", sa.Boolean()),
            sa.Column("lesson", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_ai_memory_symbol_created", ["symbol", "created_at"]),
        ("asset_analysis", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("trend", sa.String(20), nullable=False),
            sa.Column("risk", sa.String(20), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("recommendation", sa.String(30), nullable=False),
            sa.Column("indicators", postgresql.JSONB()),
            sa.Column("strength_score", sa.Float()),
            sa.Column("reversal_probability", sa.Float()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_asset_analysis_symbol_created", ["symbol", "created_at"]),
    ]

    for table_name, columns, index_name, index_cols in tables:
        op.create_table(table_name, *columns)
        op.create_index(index_name, table_name, index_cols)


def downgrade() -> None:
    for table in reversed([
        "asset_analysis", "ai_memory", "macro_indicators", "ai_consensus",
        "news_analysis", "portfolio_analysis", "market_regimes",
        "sentiment_history", "ai_explanations", "ai_decisions",
    ]):
        op.drop_table(table)
