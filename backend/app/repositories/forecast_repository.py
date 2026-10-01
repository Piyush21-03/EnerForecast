"""Database access for forecasts and prediction logs."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.database_models import Forecast, PredictionLog

logger = logging.getLogger(__name__)

SORT_COLUMNS = {
    "created_at": Forecast.created_at,
    "prediction_timestamp": Forecast.prediction_timestamp,
    "predicted_energy_kwh": Forecast.predicted_energy_kwh,
    "horizon": Forecast.horizon,
}


class ForecastRepository:
    def save_forecasts(
        self,
        db: Session,
        *,
        request_id: str,
        origin: datetime,
        horizon: int,
        model_version: str,
        points: Sequence[tuple[datetime, float]],
    ) -> int:
        """Insert one row per forecast point in a single transaction."""
        try:
            db.add_all(
                Forecast(
                    forecast_timestamp=origin,
                    prediction_timestamp=ts,
                    predicted_energy_kwh=value,
                    model_version=model_version,
                    horizon=horizon,
                    request_id=request_id,
                )
                for ts, value in points
            )
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("Failed to save forecasts")
            raise PersistenceError("Could not save forecast to the database") from exc
        return len(points)

    def add_prediction_log(
        self,
        db: Session,
        *,
        request_id: str,
        endpoint: str,
        payload: dict[str, Any] | None,
        status: str,
        error_message: str | None,
        latency_ms: float | None,
        model_version: str | None,
    ) -> None:
        try:
            db.add(
                PredictionLog(
                    request_id=request_id,
                    endpoint=endpoint,
                    request_payload=payload,
                    status=status,
                    error_message=error_message,
                    latency_ms=latency_ms,
                    model_version=model_version,
                )
            )
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("Failed to write prediction log")
            raise PersistenceError("Could not write prediction log") from exc

    def list_forecasts(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        sort_by: str = "created_at",
        order: str = "desc",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Forecast], int]:
        """Paginated, sortable forecast rows, optionally filtered by creation date (inclusive)."""
        if sort_by not in SORT_COLUMNS:
            raise ValueError(f"Unsupported sort column: {sort_by}")
        column = SORT_COLUMNS[sort_by]
        direction = column.asc() if order == "asc" else column.desc()

        filters = []
        if date_from is not None:
            filters.append(Forecast.created_at >= datetime.combine(date_from, time.min))
        if date_to is not None:
            filters.append(Forecast.created_at < datetime.combine(date_to + timedelta(days=1), time.min))

        try:
            total = db.execute(select(func.count()).select_from(Forecast).where(*filters)).scalar_one()
            stmt = (
                select(Forecast)
                .where(*filters)
                .order_by(direction, Forecast.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = list(db.execute(stmt).scalars())
        except SQLAlchemyError as exc:
            logger.exception("Failed to read forecast history")
            raise PersistenceError("Could not read forecast history from the database") from exc
        return rows, int(total)
