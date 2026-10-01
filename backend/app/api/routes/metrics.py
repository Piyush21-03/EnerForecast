from fastapi import APIRouter, Depends

from app.api.deps import get_model_service
from app.models.schemas import MetricsResponse
from app.services.model_service import ModelService

router = APIRouter(tags=["model"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics(service: ModelService = Depends(get_model_service)) -> MetricsResponse:
    """Metrics exactly as exported by the training notebook (never computed or invented here)."""
    return MetricsResponse(
        model_version=service.model_version,
        metrics=service.get_metrics(),
        feature_importance=service.get_feature_importance(),
    )
