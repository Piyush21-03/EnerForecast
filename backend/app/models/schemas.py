"""Pydantic request/response schemas for the REST API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Allow field names such as `model_version` without pydantic warnings.
_BASE_CONFIG = ConfigDict(protected_namespaces=())


class ApiModel(BaseModel):
    model_config = _BASE_CONFIG


# ------------------------------------------------------------------ predict
class PredictRequest(ApiModel):
    timestamp: datetime = Field(description="Forecast origin: the last observed hour (naive, on the hour).")
    horizon: int = Field(default=24, ge=1, le=168, description="Hours to forecast (1-168).")


class ForecastPointSchema(ApiModel):
    timestamp: datetime
    predicted_energy_kwh: float


class PredictResponse(ApiModel):
    request_id: str
    model: str
    model_version: str
    horizon: int
    unit: str
    forecast_timestamp: datetime
    forecast: list[ForecastPointSchema]


class BatchPredictRequest(ApiModel):
    requests: list[PredictRequest] = Field(min_length=1, max_length=10)


class BatchPredictItem(ApiModel):
    index: int
    success: bool
    result: PredictResponse | None = None
    error: str | None = None


class BatchPredictResponse(ApiModel):
    results: list[BatchPredictItem]


# ------------------------------------------------------------ health / model
class HealthResponse(ApiModel):
    status: str  # "ok" | "degraded"
    model_loaded: bool
    history_loaded: bool
    database_ok: bool


class ModelInfoResponse(ApiModel):
    model_name: str
    model_version: str
    dataset: str
    target: str
    unit: str
    frequency: str
    feature_count: int
    feature_columns: list[str]
    loaded_at: str | None
    config: dict[str, Any]


class MetricsResponse(ApiModel):
    model_version: str
    metrics: dict[str, Any] | None  # None when metrics.json was not exported
    feature_importance: list[dict[str, Any]]


# ------------------------------------------------------------------ history
class ForecastHistoryItem(ApiModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    forecast_timestamp: datetime
    prediction_timestamp: datetime
    predicted_energy_kwh: float
    model_version: str
    horizon: int
    request_id: str
    created_at: datetime


class ForecastHistoryResponse(ApiModel):
    items: list[ForecastHistoryItem]
    total: int
    page: int
    page_size: int
