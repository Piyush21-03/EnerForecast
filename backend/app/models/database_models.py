"""ORM tables: dataset_metadata, model_metadata, forecasts, prediction_logs."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite in tests).
JsonType = JSON().with_variant(JSONB(), "postgresql")


class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str | None] = mapped_column(String(500))
    timestamp_column: Mapped[str] = mapped_column(String(100), default="timestamp")
    target_column: Mapped[str] = mapped_column(String(100), default="energy_kwh")
    frequency: Mapped[str | None] = mapped_column(String(50))
    # Filled from the validated dataset, never guessed.
    row_count: Mapped[int | None] = mapped_column(Integer)
    start_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    end_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(100), unique=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    metrics: Mapped[dict | None] = mapped_column(JsonType)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecasts_created_at", "created_at"),
        Index("ix_forecasts_prediction_timestamp", "prediction_timestamp"),
        Index("ix_forecasts_request_id", "request_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Forecast origin: the timestamp the forecast was issued from.
    forecast_timestamp: Mapped[datetime] = mapped_column(DateTime)
    # The future hour this row predicts.
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime)
    predicted_energy_kwh: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(100))
    # Added beyond the base spec so the History page can show horizon
    # and group the rows of one request.
    horizon: Mapped[int] = mapped_column(Integer)
    request_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    __table_args__ = (Index("ix_prediction_logs_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36))
    endpoint: Mapped[str] = mapped_column(String(100))
    request_payload: Mapped[dict | None] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(20))  # "success" | "error"
    error_message: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
