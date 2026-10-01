"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "dataset_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source", sa.String(500)),
        sa.Column("timestamp_column", sa.String(100), nullable=False),
        sa.Column("target_column", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(50)),
        sa.Column("row_count", sa.Integer()),
        sa.Column("start_timestamp", sa.DateTime()),
        sa.Column("end_timestamp", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "model_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False, unique=True),
        sa.Column("artifact_path", sa.String(500)),
        sa.Column("metrics", json_type),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("forecast_timestamp", sa.DateTime(), nullable=False),
        sa.Column("prediction_timestamp", sa.DateTime(), nullable=False),
        sa.Column("predicted_energy_kwh", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_forecasts_created_at", "forecasts", ["created_at"])
    op.create_index("ix_forecasts_prediction_timestamp", "forecasts", ["prediction_timestamp"])
    op.create_index("ix_forecasts_request_id", "forecasts", ["request_id"])
    op.create_table(
        "prediction_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("endpoint", sa.String(100), nullable=False),
        sa.Column("request_payload", json_type),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("model_version", sa.String(100)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prediction_logs_created_at", "prediction_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_prediction_logs_created_at", table_name="prediction_logs")
    op.drop_table("prediction_logs")
    op.drop_index("ix_forecasts_request_id", table_name="forecasts")
    op.drop_index("ix_forecasts_prediction_timestamp", table_name="forecasts")
    op.drop_index("ix_forecasts_created_at", table_name="forecasts")
    op.drop_table("forecasts")
    op.drop_table("model_metadata")
    op.drop_table("dataset_metadata")
