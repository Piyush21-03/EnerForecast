"""Database access for model_metadata and dataset_metadata."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.database_models import DatasetMetadata, ModelMetadata

logger = logging.getLogger(__name__)


class ModelRepository:
    def register_model(
        self,
        db: Session,
        *,
        model_name: str,
        model_version: str,
        artifact_path: str | None,
        metrics: dict[str, Any] | None,
    ) -> ModelMetadata:
        """Insert or update the row for this version and make it the only active model."""
        try:
            row = db.execute(select(ModelMetadata).where(ModelMetadata.model_version == model_version)).scalar_one_or_none()
            if row is None:
                row = ModelMetadata(model_name=model_name, model_version=model_version, is_active=True)
                db.add(row)
            row.model_name = model_name
            row.artifact_path = artifact_path
            row.metrics = metrics
            row.is_active = True
            db.execute(
                update(ModelMetadata).where(ModelMetadata.model_version != model_version).values(is_active=False)
            )
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("Failed to register model metadata")
            raise PersistenceError("Could not record model metadata") from exc
        return row

    def get_active_model(self, db: Session) -> ModelMetadata | None:
        try:
            return db.execute(
                select(ModelMetadata).where(ModelMetadata.is_active.is_(True)).order_by(ModelMetadata.id.desc())
            ).scalars().first()
        except SQLAlchemyError as exc:
            logger.exception("Failed to read active model")
            raise PersistenceError("Could not read model metadata") from exc

    def register_dataset(
        self,
        db: Session,
        *,
        name: str,
        source: str | None,
        frequency: str | None,
        row_count: int | None,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> DatasetMetadata:
        """Insert or update the single row describing the dataset with this name."""
        try:
            row = db.execute(select(DatasetMetadata).where(DatasetMetadata.name == name)).scalar_one_or_none()
            if row is None:
                row = DatasetMetadata(name=name)
                db.add(row)
            row.source = source
            row.frequency = frequency
            row.row_count = row_count
            row.start_timestamp = start_timestamp
            row.end_timestamp = end_timestamp
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("Failed to register dataset metadata")
            raise PersistenceError("Could not record dataset metadata") from exc
        return row
