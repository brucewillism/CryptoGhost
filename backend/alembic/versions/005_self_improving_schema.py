"""Self-improving schema v5."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_self_improving_schema"
down_revision = "004_investment_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = [
        ("meta_learning_records", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("model_name", sa.String(80), nullable=False),
            sa.Column("market_regime", sa.String(30), nullable=False),
            sa.Column("historical_accuracy", sa.Float, nullable=False),
            sa.Column("sharpe_ratio", sa.Float),
            sa.Column("weight", sa.Float, server_default="1.0"),
            sa.Column("is_best", sa.Boolean, server_default="false"),
            sa.Column("metadata", postgresql.JSONB),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_meta_learning_regime_created", ["market_regime", "created_at"]),
        ("prediction_validations", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("predicted_return_pct", sa.Float, nullable=False),
            sa.Column("actual_return_pct", sa.Float),
            sa.Column("predicted_confidence", sa.Float, nullable=False),
            sa.Column("calibration_error", sa.Float),
            sa.Column("direction_correct", sa.Boolean),
            sa.Column("validation_score", sa.Float, nullable=False),
            sa.Column("window_days", sa.Integer, server_default="7"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_prediction_validations_symbol_created", ["symbol", "created_at"]),
        ("strategy_evolutions", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("strategy_id", sa.String(50), nullable=False),
            sa.Column("generation", sa.Integer, server_default="0"),
            sa.Column("fitness_score", sa.Float, nullable=False),
            sa.Column("parameters", postgresql.JSONB, nullable=False),
            sa.Column("sharpe_ratio", sa.Float),
            sa.Column("max_drawdown_pct", sa.Float),
            sa.Column("promoted", sa.Boolean, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_strategy_evolutions_created", ["created_at"]),
        ("drift_detection_v5", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("model_name", sa.String(80), nullable=False),
            sa.Column("drift_type", sa.String(30), nullable=False),
            sa.Column("drift_score", sa.Float, nullable=False),
            sa.Column("regime_shift_detected", sa.Boolean, server_default="false"),
            sa.Column("retrain_triggered", sa.Boolean, server_default="false"),
            sa.Column("details", postgresql.JSONB),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_drift_detection_v5_model_created", ["model_name", "created_at"]),
        ("real_performance_metrics", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("portfolio_id", sa.String(50), server_default="default"),
            sa.Column("sharpe_ratio", sa.Float, nullable=False),
            sa.Column("sortino_ratio", sa.Float, nullable=False),
            sa.Column("max_drawdown_pct", sa.Float, nullable=False),
            sa.Column("cagr_pct", sa.Float, nullable=False),
            sa.Column("hit_rate", sa.Float, nullable=False),
            sa.Column("expected_vs_actual_pct", sa.Float, nullable=False),
            sa.Column("alpha_pct", sa.Float),
            sa.Column("metrics", postgresql.JSONB),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_real_performance_created", ["created_at"]),
        ("ai_truth_scores", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("truth_score", sa.Float, nullable=False),
            sa.Column("raw_confidence", sa.Float, nullable=False),
            sa.Column("corrected_confidence", sa.Float, nullable=False),
            sa.Column("overconfidence_detected", sa.Boolean, server_default="false"),
            sa.Column("hallucination_risk", sa.Float, server_default="0"),
            sa.Column("validation_basis", postgresql.JSONB, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_ai_truth_symbol_created", ["symbol", "created_at"]),
        ("self_improvement_logs", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("action_type", sa.String(50), nullable=False),
            sa.Column("target", sa.String(80), nullable=False),
            sa.Column("before_value", sa.Float),
            sa.Column("after_value", sa.Float),
            sa.Column("improvement_pct", sa.Float),
            sa.Column("details", postgresql.JSONB),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_self_improvement_created", ["created_at"]),
        ("market_state_intelligence", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("structural_state", sa.String(50), nullable=False),
            sa.Column("fragility_score", sa.Float, nullable=False),
            sa.Column("hidden_risk_score", sa.Float, nullable=False),
            sa.Column("trend_exhaustion", sa.Float, nullable=False),
            sa.Column("manipulation_score", sa.Float, nullable=False),
            sa.Column("details", postgresql.JSONB, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_market_state_symbol_created", ["symbol", "created_at"]),
        ("orderflow_snapshots", [
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("cumulative_delta", sa.Float, nullable=False),
            sa.Column("delta_imbalance", sa.Float, nullable=False),
            sa.Column("absorption_detected", sa.Boolean, server_default="false"),
            sa.Column("spoofing_detected", sa.Boolean, server_default="false"),
            sa.Column("smart_money_direction", sa.String(20), nullable=False),
            sa.Column("footprint", postgresql.JSONB, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ], "ix_orderflow_symbol_created", ["symbol", "created_at"]),
    ]
    for name, cols, idx_name, idx_cols in tables:
        op.create_table(name, *cols)
        op.create_index(idx_name, name, idx_cols)


def downgrade() -> None:
    for name in (
        "orderflow_snapshots", "market_state_intelligence", "self_improvement_logs",
        "ai_truth_scores", "real_performance_metrics", "drift_detection_v5",
        "strategy_evolutions", "prediction_validations", "meta_learning_records",
    ):
        op.drop_table(name)
