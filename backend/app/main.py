"""FastAPI application entry point.

Startup loads the trained model and hourly history once, builds the forecast
service, and (best-effort) records model/dataset metadata. Routers are mounted
in create_app(). The model is never retrained here.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import energy, forecast, health, history, metrics, model
from app.core.config import get_settings
from app.core.exceptions import ForecastServiceError, ModelArtifactError
from app.core.logging import setup_logging
from app.db.database import get_session_factory
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.model_repository import ModelRepository
from app.services.feature_service import FeatureService
from app.services.forecast_service import ForecastService
from app.services.history_provider import CsvHistoryProvider
from app.services.model_service import ModelService

logger = logging.getLogger(__name__)


def record_metadata(model_service: ModelService, history: CsvHistoryProvider, settings) -> None:
    """Best-effort: store which model/dataset this instance serves. Never blocks startup."""
    try:
        info = model_service.get_model_info()
        summary = history.summary()
        repo = ModelRepository()
        with get_session_factory()() as db:
            repo.register_model(
                db,
                model_name=str(info["model_name"]),
                model_version=str(info["model_version"]),
                artifact_path=str(settings.model_path),
                metrics=model_service.get_metrics(),
            )
            repo.register_dataset(
                db,
                name="UCI Individual Household Electric Power Consumption (hourly history)",
                source=str(settings.history_data_path),
                frequency="hourly",
                row_count=summary["rows"],
                start_timestamp=summary["start"].to_pydatetime() if summary["start"] is not None else None,
                end_timestamp=summary["end"].to_pydatetime() if summary["end"] is not None else None,
            )
    except Exception:  # noqa: BLE001 - metadata is optional; log and carry on
        logger.exception("Could not record model/dataset metadata; continuing")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the trained model and history once. The app still starts if they
    are unavailable, so /health can report the problem instead of crashing."""
    settings = get_settings()
    model_service = ModelService.from_settings(settings)
    app.state.model_service = model_service
    app.state.forecast_service = None
    app.state.history = None
    try:
        model_service.load()
        history = CsvHistoryProvider(settings.history_data_path)
        app.state.history = history
        features = FeatureService(model_service.feature_columns)
        app.state.forecast_service = ForecastService(model_service, features, history, ForecastRepository())
        record_metadata(model_service, history, settings)
    except (ModelArtifactError, ForecastServiceError):
        logger.exception("Startup incomplete; predictions are unavailable")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    for module in (health, forecast, model, metrics, history, energy):
        app.include_router(module.router)
    logger.info("Application created (env=%s)", settings.app_env)
    return app


app = create_app()
