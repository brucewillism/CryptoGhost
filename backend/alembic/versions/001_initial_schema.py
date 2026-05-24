"""Initial CryptoGhost schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(20, 8), nullable=False),
        sa.Column("high", sa.Numeric(20, 8), nullable=False),
        sa.Column("low", sa.Numeric(20, 8), nullable=False),
        sa.Column("close", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(30, 8), nullable=False),
        sa.Column("bid", sa.Numeric(20, 8)),
        sa.Column("ask", sa.Numeric(20, 8)),
        sa.Column("indicators", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_market_data_symbol_timestamp", "market_data", ["symbol", "timestamp"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("order_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8)),
        sa.Column("filled_quantity", sa.Numeric(20, 8), default=0),
        sa.Column("average_price", sa.Numeric(20, 8)),
        sa.Column("stop_loss", sa.Numeric(20, 8)),
        sa.Column("take_profit", sa.Numeric(20, 8)),
        sa.Column("trailing_stop_pct", sa.Float()),
        sa.Column("trading_mode", sa.String(10), default="paper"),
        sa.Column("external_id", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exchange", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("current_price", sa.Numeric(20, 8)),
        sa.Column("stop_loss", sa.Numeric(20, 8)),
        sa.Column("take_profit", sa.Numeric(20, 8)),
        sa.Column("trailing_stop_pct", sa.Float()),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), default=0),
        sa.Column("trading_mode", sa.String(10), default="paper"),
        sa.Column("is_open", sa.Boolean(), default=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ai_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("predicted_price", sa.Numeric(20, 8)),
        sa.Column("features", postgresql.JSONB()),
        sa.Column("metrics", postgresql.JSONB()),
        sa.Column("explanation", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("actor", sa.String(100), default="system"),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_event_type_created", "audit_logs", ["event_type", "created_at"])

    op.create_table(
        "risk_state",
        sa.Column("id", sa.Integer(), primary_key=True, default=1),
        sa.Column("daily_pnl", sa.Numeric(20, 8), default=0),
        sa.Column("daily_loss_limit_hit", sa.Boolean(), default=False),
        sa.Column("circuit_breaker_active", sa.Boolean(), default=False),
        sa.Column("total_exposure", sa.Numeric(20, 8), default=0),
        sa.Column("max_exposure", sa.Numeric(20, 8), default=0),
        sa.Column("trading_halted", sa.Boolean(), default=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "broker_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("broker", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("fee_score", sa.Float(), default=0),
        sa.Column("spread_score", sa.Float(), default=0),
        sa.Column("liquidity_score", sa.Float(), default=0),
        sa.Column("slippage_score", sa.Float(), default=0),
        sa.Column("execution_score", sa.Float(), default=0),
        sa.Column("api_stability_score", sa.Float(), default=0),
        sa.Column("total_score", sa.Float(), default=0),
        sa.Column("is_selected", sa.Boolean(), default=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("broker_scores")
    op.drop_table("risk_state")
    op.drop_index("ix_audit_logs_event_type_created", "audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("ai_predictions")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_index("ix_market_data_symbol_timestamp", "market_data")
    op.drop_table("market_data")
