"""Quant v6 schema migration."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_quant_v6_schema"
down_revision = "005_self_improving_schema"
branch_labels = None
depends_on = None


def _create(name, columns, index_name=None, index_cols=None):
    op.create_table(name, *columns)
    if index_name and index_cols:
        op.create_index(index_name, name, index_cols)


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    ts = sa.DateTime(timezone=True)
    _create("feature_snapshots", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("timeframe", sa.String(10), server_default="1h"),
        sa.Column("timestamp", ts, nullable=False),
        sa.Column("features", postgresql.JSONB, nullable=False),
        sa.Column("schema_version", sa.String(20), server_default="v6.0"),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_feature_snapshots_symbol_tf_ts", ["symbol", "timeframe", "timestamp"])

    _create("market_signals_v6", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("final_score", sa.Float, nullable=False),
        sa.Column("classification", sa.String(20), nullable=False),
        sa.Column("final_decision", sa.String(10), nullable=False),
        sa.Column("consensus", sa.Float, nullable=False),
        sa.Column("calibrated_confidence", sa.Float, nullable=False),
        sa.Column("technical_score", sa.Float, server_default="0"),
        sa.Column("sentiment_score", sa.Float, server_default="0"),
        sa.Column("regime_alignment", sa.Float, server_default="0"),
        sa.Column("agreement", sa.Integer, server_default="0"),
        sa.Column("disagreement", sa.Integer, server_default="0"),
        sa.Column("conflicts", postgresql.JSONB),
        sa.Column("agent_votes", postgresql.JSONB),
        sa.Column("can_execute", sa.Boolean, server_default="false"),
        sa.Column("rejection_reasons", postgresql.JSONB),
        sa.Column("regime", sa.String(30)),
        sa.Column("expires_at", ts),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_market_signals_v6_symbol_created", ["symbol", "created_at"])

    _create("agent_performance", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("symbol", sa.String(30), server_default="*"),
        sa.Column("timeframe", sa.String(10), server_default="1h"),
        sa.Column("regime", sa.String(30), server_default="*"),
        sa.Column("accuracy", sa.Float, nullable=False),
        sa.Column("sample_count", sa.Integer, server_default="0"),
        sa.Column("dynamic_weight", sa.Float, server_default="0.2"),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("updated_at", ts, server_default=sa.func.now()),
    ], "ix_agent_performance_agent_regime", ["agent_name", "regime", "symbol"])

    _create("trade_memory", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("asset", sa.String(30), nullable=False),
        sa.Column("regime", sa.String(30), nullable=False),
        sa.Column("setup", sa.String(50), server_default="unknown"),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("exit_price", sa.Float),
        sa.Column("pnl", sa.Float, server_default="0"),
        sa.Column("duration_hours", sa.Float, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("consensus", sa.Float, nullable=False),
        sa.Column("features_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("result", sa.String(20), server_default="open"),
        sa.Column("market_conditions", postgresql.JSONB),
        sa.Column("order_id", sa.String(50)),
        sa.Column("created_at", ts, server_default=sa.func.now()),
        sa.Column("closed_at", ts),
    ], "ix_trade_memory_asset_created", ["asset", "created_at"])

    _create("trade_memory_embeddings", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("trade_memory_id", uuid, nullable=False),
        sa.Column("embedding", postgresql.JSONB),
        sa.Column("label", sa.String(50)),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_trade_memory_emb_trade", ["trade_memory_id"])

    _create("backtest_runs", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbols", postgresql.JSONB, nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=False),
        sa.Column("metrics", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_backtest_runs_created", ["created_at"])

    _create("backtest_trades", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("run_id", uuid, nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("exit_price", sa.Float),
        sa.Column("pnl", sa.Float, server_default="0"),
        sa.Column("slippage", sa.Float, server_default="0"),
        sa.Column("fees", sa.Float, server_default="0"),
        sa.Column("opened_at", ts),
        sa.Column("closed_at", ts),
    ], "ix_backtest_trades_run", ["run_id"])

    _create("portfolio_snapshots", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("portfolio_id", sa.String(50), server_default="paper"),
        sa.Column("total_value_usdt", sa.Float, nullable=False),
        sa.Column("exposure_pct", sa.Float, server_default="0"),
        sa.Column("heat_score", sa.Float, server_default="0"),
        sa.Column("open_positions", sa.Integer, server_default="0"),
        sa.Column("daily_pnl", sa.Float, server_default="0"),
        sa.Column("details", postgresql.JSONB),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_portfolio_snapshots_created", ["created_at"])

    _create("regime_history_v6", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("regime", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("policy_applied", postgresql.JSONB),
        sa.Column("features", postgresql.JSONB),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_regime_history_v6_symbol_created", ["symbol", "created_at"])

    _create("sentiment_v2_history", [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("sources", postgresql.JSONB),
        sa.Column("news_impact", sa.Float, server_default="0"),
        sa.Column("method", sa.String(30), server_default="lexical"),
        sa.Column("created_at", ts, server_default=sa.func.now()),
    ], "ix_sentiment_v2_symbol_created", ["symbol", "created_at"])


def downgrade() -> None:
    for table in (
        "sentiment_v2_history", "regime_history_v6", "portfolio_snapshots",
        "backtest_trades", "backtest_runs", "trade_memory_embeddings",
        "trade_memory", "agent_performance", "market_signals_v6", "feature_snapshots",
    ):
        op.drop_table(table)
