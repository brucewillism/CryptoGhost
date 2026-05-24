"""Investment prioritization schema v4."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_investment_schema"
down_revision = "003_quant_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("asset_class", sa.String(20), server_default="crypto"),
        sa.Column("priority_score", sa.Float, nullable=False),
        sa.Column("rank_position", sa.Integer, nullable=False),
        sa.Column("expected_return_pct", sa.Float, nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("recommendation", sa.String(40), nullable=False),
        sa.Column("reasons", postgresql.JSONB),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_investment_rankings_symbol_created", "investment_rankings", ["symbol", "created_at"])

    op.create_table(
        "opportunity_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("opportunity_score", sa.Float, nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("components", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_scores_symbol_created", "opportunity_scores", ["symbol", "created_at"])

    op.create_table(
        "expected_returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("expected_return_pct", sa.Float, nullable=False),
        sa.Column("drawdown_probable_pct", sa.Float, nullable=False),
        sa.Column("upside_downside_ratio", sa.Float, nullable=False),
        sa.Column("horizon_days", sa.Integer, server_default="14"),
        sa.Column("confidence_interval", postgresql.JSONB, nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_expected_returns_symbol_created", "expected_returns", ["symbol", "created_at"])

    op.create_table(
        "institutional_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("strength", sa.Float, nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_institutional_signals_symbol_created", "institutional_signals", ["symbol", "created_at"])

    op.create_table(
        "probabilistic_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("bullish_probability", sa.Float, nullable=False),
        sa.Column("bearish_probability", sa.Float, nullable=False),
        sa.Column("sideways_probability", sa.Float, nullable=False),
        sa.Column("uncertainty", sa.Float, nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_probabilistic_predictions_symbol_created", "probabilistic_predictions", ["symbol", "created_at"])

    op.create_table(
        "adaptive_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("portfolio_id", sa.String(50), server_default="default"),
        sa.Column("allocations", postgresql.JSONB, nullable=False),
        sa.Column("total_exposure_pct", sa.Float, nullable=False),
        sa.Column("cash_pct", sa.Float, nullable=False),
        sa.Column("regime", sa.String(30)),
        sa.Column("rationale", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_adaptive_allocations_created", "adaptive_allocations", ["created_at"])

    op.create_table(
        "alpha_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("alpha_score", sa.Float, nullable=False),
        sa.Column("alpha_type", sa.String(50), nullable=False),
        sa.Column("expected_edge_pct", sa.Float, nullable=False),
        sa.Column("rarity", sa.String(20), server_default="moderate"),
        sa.Column("details", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alpha_detections_symbol_created", "alpha_detections", ["symbol", "created_at"])


def downgrade() -> None:
    for table in (
        "alpha_detections", "adaptive_allocations", "probabilistic_predictions",
        "institutional_signals", "expected_returns", "opportunity_scores", "investment_rankings",
    ):
        op.drop_table(table)
