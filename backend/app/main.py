"""FastAPI application entry point.

Phase 7: configuration, logging, CORS, one-time startup wiring of the model,
hourly history and forecast service, plus the REST routers.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import forecast, health, history, metrics, model
from app.core.config import get_settings
from app.core.exceptions import ForecastServiceError, ModelArtifactError
from app.core.logging import setup_logging
from app.repositories.forecast_repository import ForecastRepository
from app.services.feature_service import FeatureService
from app.services.forecast_service import ForecastService
from app.services.history_provider import CsvHistoryProvider
from app.services.model_service import ModelService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the trained model and history once. The app still starts if they
    are unavailable, so /health can report the problem instead of crashing."""
    settings = get_settings()
    model_service = ModelService.from_settings(settings)
    app.state.model_service = model_service
    app.state.forecast_service = None
    try:
        model_service.load()
        history = CsvHistoryProvider(settings.history_data_path)
        features = FeatureService(model_service.feature_columns)
        app.state.forecast_service = ForecastService(model_service, features, history, ForecastRepository())
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
    for module in (health, forecast, model, metrics, history):
        app.include_router(module.router)
    logger.info("Application created (env=%s)", settings.app_env)
    return app


app = create_app()
