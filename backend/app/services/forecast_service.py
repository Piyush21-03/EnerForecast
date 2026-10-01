"""Recursive multi-step forecasting with the pre-trained model.

Convention: the request `timestamp` is the forecast ORIGIN, i.e. the last
observed hour (inclusive). The forecast covers origin+1h ... origin+horizon h.
Only observations at or before the origin are used, even if the history file
contains later data (so past origins can be back-tested honestly).

Each step builds features from real history plus the model's own earlier
predictions (recursive forecasting); actual future targets are never used.
The model is never retrained here.
"""

from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

from app.core.exceptions import (
    FeatureMismatchError,
    ForecastComputationError,
    ForecastInputError,
    InsufficientHistoryError,
    InvalidHorizonError,
    InvalidTimestampError,
    PersistenceError,
)
from app.services.feature_service import HOUR, FeatureService
from app.services.history_provider import HistoryProvider

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.repositories.forecast_repository import ForecastRepository
    from app.services.model_service import ModelService

logger = logging.getLogger(__name__)

MIN_HORIZON = 1
MAX_HORIZON = 168
UNIT = "kWh"


@dataclass(frozen=True)
class ForecastPoint:
    timestamp: pd.Timestamp
    predicted_energy_kwh: float


@dataclass(frozen=True)
class ForecastResult:
    request_id: str
    model: str
    model_version: str
    horizon: int
    unit: str
    origin: pd.Timestamp
    points: list[ForecastPoint]


class ForecastService:
    def __init__(
        self,
        model_service: ModelService,
        feature_service: FeatureService,
        history: HistoryProvider,
        repository: ForecastRepository | None = None,
    ) -> None:
        if feature_service.feature_columns != model_service.feature_columns:
            raise FeatureMismatchError(
                "FeatureService columns differ from the model's feature_columns.json (names or order)"
            )
        self._model = model_service
        self._features = feature_service
        self._history = history
        self._repository = repository

    # ------------------------------------------------------------- validation
    @staticmethod
    def parse_origin(timestamp: Any) -> pd.Timestamp:
        try:
            ts = pd.Timestamp(timestamp)
        except (ValueError, TypeError) as exc:
            raise InvalidTimestampError(f"Invalid timestamp: {timestamp!r}") from exc
        if pd.isna(ts):
            raise InvalidTimestampError(f"Invalid timestamp: {timestamp!r}")
        if ts.tzinfo is not None:
            raise InvalidTimestampError("Timestamp must be timezone-naive")
        if ts != ts.floor("h"):
            raise InvalidTimestampError(f"Timestamp {ts} must be aligned to the hour")
        return ts

    @staticmethod
    def validate_horizon(horizon: Any) -> int:
        if isinstance(horizon, bool) or not isinstance(horizon, int) or not MIN_HORIZON <= horizon <= MAX_HORIZON:
            raise InvalidHorizonError(f"horizon must be an integer between {MIN_HORIZON} and {MAX_HORIZON}")
        return horizon

    # --------------------------------------------------------------- forecast
    def forecast(self, timestamp: Any, horizon: int, request_id: str | None = None) -> ForecastResult:
        """Pure computation: no database access."""
        origin = self.parse_origin(timestamp)
        horizon = self.validate_horizon(horizon)

        latest = self._history.latest_timestamp()
        if latest is None or origin > latest:
            raise InsufficientHistoryError(
                f"Origin {origin} is after the last available history ({latest}); cannot forecast without observations"
            )

        lookback = self._features.required_lookback_hours
        working = self._history.get_window(origin, lookback) if lookback else pd.Series(dtype=float)
        working = working.astype(float).copy()

        points: list[ForecastPoint] = []
        for step in range(1, horizon + 1):
            ts = origin + step * HOUR
            row = self._features.build_row(working, ts)
            frame = pd.DataFrame([row], columns=self._features.feature_columns)
            value = float(self._model.predict(frame)[0])
            if not math.isfinite(value):
                raise ForecastComputationError(f"Model returned a non-finite prediction for {ts}")
            working.loc[ts] = value  # feed the prediction back as history for the next step
            points.append(ForecastPoint(timestamp=ts, predicted_energy_kwh=value))

        info = self._model.get_model_info()
        return ForecastResult(
            request_id=request_id or str(uuid.uuid4()),
            model=str(info["model_name"]),
            model_version=str(info["model_version"]),
            horizon=horizon,
            unit=UNIT,
            origin=origin,
            points=points,
        )

    def forecast_and_store(self, db: Session, timestamp: Any, horizon: int, endpoint: str = "/predict") -> ForecastResult:
        """Forecast, persist the points, and write a prediction log entry."""
        if self._repository is None:
            raise RuntimeError("ForecastService has no repository configured")
        request_id = str(uuid.uuid4())
        payload = {"timestamp": str(timestamp), "horizon": horizon}
        started = time.perf_counter()
        try:
            result = self.forecast(timestamp, horizon, request_id=request_id)
            self._repository.save_forecasts(
                db,
                request_id=request_id,
                origin=result.origin.to_pydatetime(),
                horizon=result.horizon,
                model_version=result.model_version,
                points=[(p.timestamp.to_pydatetime(), p.predicted_energy_kwh) for p in result.points],
            )
        except (ForecastInputError, PersistenceError, ForecastComputationError) as exc:
            self._log(db, request_id, endpoint, payload, "error", str(exc), started)
            raise
        self._log(db, request_id, endpoint, payload, "success", None, started, result.model_version)
        return result

    def _log(
        self,
        db: Session,
        request_id: str,
        endpoint: str,
        payload: dict[str, Any],
        status: str,
        error: str | None,
        started: float,
        model_version: str | None = None,
    ) -> None:
        assert self._repository is not None
        try:
            self._repository.add_prediction_log(
                db,
                request_id=request_id,
                endpoint=endpoint,
                payload=payload,
                status=status,
                error_message=error,
                latency_ms=(time.perf_counter() - started) * 1000,
                model_version=model_version,
            )
        except PersistenceError:
            logger.warning("Prediction log could not be saved for request %s", request_id)
