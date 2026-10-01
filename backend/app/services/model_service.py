"""Loads the model exported from Google Colab and runs inference.

The model is loaded ONCE at application startup and never retrained here.

Artifact contract (produced by the training notebook):
  model file        joblib dump of a fitted estimator with .predict()
  model_config.json JSON object; requires "model_name" and "model_version",
                    any other keys are passed through to /model-info
  feature_columns.json  JSON list of column names, in training order
                    (or {"feature_columns": [...]})
  metrics.json      optional JSON object (missing -> metrics reported as None)
  feature_importance.csv  optional CSV (missing -> empty list)

Security: joblib uses pickle. Only load artifacts you produced yourself.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.exceptions import (
    ArtifactNotFoundError,
    FeatureMismatchError,
    InvalidArtifactError,
    ModelNotLoadedError,
)

logger = logging.getLogger(__name__)

REQUIRED_CONFIG_KEYS = ("model_name", "model_version")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidArtifactError(f"Cannot read JSON artifact {path.name}: {exc}") from exc


class ModelService:
    def __init__(
        self,
        model_path: Path,
        model_config_path: Path,
        feature_columns_path: Path,
        metrics_path: Path,
        feature_importance_path: Path,
    ) -> None:
        self._model_path = Path(model_path)
        self._config_path = Path(model_config_path)
        self._features_path = Path(feature_columns_path)
        self._metrics_path = Path(metrics_path)
        self._importance_path = Path(feature_importance_path)

        self._model: Any = None
        self._config: dict[str, Any] = {}
        self._feature_columns: list[str] = []
        self._metrics: dict[str, Any] | None = None
        self._feature_importance: list[dict[str, Any]] = []
        self._loaded_at: datetime | None = None

    @classmethod
    def from_settings(cls, settings: Any) -> ModelService:
        return cls(
            model_path=settings.model_path,
            model_config_path=settings.model_config_path,
            feature_columns_path=settings.feature_columns_path,
            metrics_path=settings.metrics_path,
            feature_importance_path=settings.feature_importance_path,
        )

    # ------------------------------------------------------------------ loading
    def load(self) -> None:
        required = [self._model_path, self._config_path, self._features_path]
        missing = [str(p) for p in required if not p.is_file()]
        if missing:
            raise ArtifactNotFoundError(f"Missing required artifact file(s): {', '.join(missing)}")

        config = _read_json(self._config_path)
        if not isinstance(config, dict):
            raise InvalidArtifactError("model_config.json must be a JSON object")
        absent = [k for k in REQUIRED_CONFIG_KEYS if k not in config]
        if absent:
            raise InvalidArtifactError(f"model_config.json is missing key(s): {', '.join(absent)}")

        columns = _read_json(self._features_path)
        if isinstance(columns, dict):
            columns = columns.get("feature_columns")
        if (
            not isinstance(columns, list)
            or not columns
            or not all(isinstance(c, str) for c in columns)
            or len(set(columns)) != len(columns)
        ):
            raise InvalidArtifactError(
                "feature_columns.json must be a non-empty list of unique column names"
            )

        try:
            model = joblib.load(self._model_path)
        except Exception as exc:  # unpickling can fail in many ways
            raise InvalidArtifactError(f"Cannot load model file {self._model_path.name}: {exc}") from exc
        if not hasattr(model, "predict"):
            raise InvalidArtifactError("Loaded model object has no predict() method")

        trained_names = self._model_feature_names(model)
        if trained_names is None:
            logger.warning("Model does not expose feature names; skipping name check against feature_columns.json")
        elif trained_names != columns:
            raise FeatureMismatchError(self._describe_mismatch(trained_names, columns, "model", "feature_columns.json"))

        self._model = model
        self._config = config
        self._feature_columns = columns
        self._metrics = self._load_metrics()
        self._feature_importance = self._load_feature_importance()
        self._loaded_at = datetime.now(timezone.utc)
        logger.info(
            "Model loaded: %s (%s), %d features",
            config["model_name"], config["model_version"], len(columns),
        )

    def _load_metrics(self) -> dict[str, Any] | None:
        if not self._metrics_path.is_file():
            logger.warning("metrics.json not found; metrics will be reported as unavailable")
            return None
        data = _read_json(self._metrics_path)
        if not isinstance(data, dict):
            raise InvalidArtifactError("metrics.json must be a JSON object")
        return data

    def _load_feature_importance(self) -> list[dict[str, Any]]:
        if not self._importance_path.is_file():
            logger.warning("feature_importance.csv not found")
            return []
        try:
            with self._importance_path.open(newline="", encoding="utf-8") as fh:
                return list(csv.DictReader(fh))
        except (OSError, csv.Error) as exc:
            raise InvalidArtifactError(f"Cannot read feature_importance.csv: {exc}") from exc

    @staticmethod
    def _model_feature_names(model: Any) -> list[str] | None:
        """Feature names stored in the fitted model, if it exposes them."""
        for attr in ("feature_names_in_", "feature_name_"):  # scikit-learn / LightGBM sklearn API
            names = getattr(model, attr, None)
            if names is not None:
                return [str(n) for n in names]
        booster = getattr(model, "booster_", model)  # LightGBM Booster
        fn = getattr(booster, "feature_name", None)
        if callable(fn):
            return [str(n) for n in fn()]
        return None

    # --------------------------------------------------------------- inference
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def feature_columns(self) -> list[str]:
        self._require_loaded()
        return list(self._feature_columns)

    @property
    def model_version(self) -> str:
        self._require_loaded()
        return str(self._config["model_version"])

    def validate_features(self, columns: list[str]) -> None:
        self._require_loaded()
        columns = list(columns)
        if columns != self._feature_columns:
            raise FeatureMismatchError(
                self._describe_mismatch(columns, self._feature_columns, "input", "feature_columns.json")
            )

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Predict energy_kwh for each row. Columns must match training exactly."""
        self._require_loaded()
        if features.empty:
            raise FeatureMismatchError("Input feature frame has no rows")
        self.validate_features(list(features.columns))
        return np.asarray(self._model.predict(features), dtype=float)

    # ---------------------------------------------------------------- metadata
    def get_model_info(self) -> dict[str, Any]:
        self._require_loaded()
        return {
            "model_name": self._config["model_name"],
            "model_version": self._config["model_version"],
            "feature_count": len(self._feature_columns),
            "feature_columns": list(self._feature_columns),
            "config": dict(self._config),
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
        }

    def get_metrics(self) -> dict[str, Any] | None:
        self._require_loaded()
        return self._metrics

    def get_feature_importance(self) -> list[dict[str, Any]]:
        self._require_loaded()
        return list(self._feature_importance)

    # ----------------------------------------------------------------- helpers
    def _require_loaded(self) -> None:
        if self._model is None:
            raise ModelNotLoadedError("Model is not loaded")

    @staticmethod
    def _describe_mismatch(actual: list[str], expected: list[str], actual_name: str, expected_name: str) -> str:
        missing = [c for c in expected if c not in actual]
        unexpected = [c for c in actual if c not in expected]
        parts = [f"Feature mismatch between {actual_name} and {expected_name}."]
        if missing:
            parts.append(f"Missing: {missing}.")
        if unexpected:
            parts.append(f"Unexpected: {unexpected}.")
        if not missing and not unexpected:
            parts.append("Same columns but different order.")
        return " ".join(parts)
