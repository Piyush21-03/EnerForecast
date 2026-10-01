from fastapi import APIRouter, Depends

from app.api.deps import get_model_service
from app.models.schemas import ModelInfoResponse
from app.services.model_service import ModelService

router = APIRouter(tags=["model"])

DATASET_NAME = "UCI Individual Household Electric Power Consumption"


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(service: ModelService = Depends(get_model_service)) -> ModelInfoResponse:
    info = service.get_model_info()
    return ModelInfoResponse(
        model_name=str(info["model_name"]),
        model_version=str(info["model_version"]),
        dataset=DATASET_NAME,
        target="energy_kwh",
        unit="kWh",
        frequency="Hourly",
        feature_count=info["feature_count"],
        feature_columns=info["feature_columns"],
        loaded_at=info["loaded_at"],
        config=info["config"],
    )
