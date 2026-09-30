"""FastAPI dependencies that expose services created at startup."""

from fastapi import Request

from app.core.exceptions import ModelNotLoadedError
from app.repositories.forecast_repository import ForecastRepository
from app.services.forecast_service import ForecastService
from app.services.model_service import ModelService


def get_forecast_service(request: Request) -> ForecastService:
    service = getattr(request.app.state, "forecast_service", None)
    if service is None:
        raise ModelNotLoadedError("Forecast service unavailable: model artifacts or hourly history not loaded")
    return service


def get_model_service(request: Request) -> ModelService:
    service = getattr(request.app.state, "model_service", None)
    if service is None or not service.is_loaded:
        raise ModelNotLoadedError("Model is not loaded")
    return service


def get_forecast_repository() -> ForecastRepository:
    return ForecastRepository()
