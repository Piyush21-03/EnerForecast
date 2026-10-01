"""ArtifactManager — downloads model artifacts from Neon Object Storage on startup.

The manager pulls files from the bucket only when they are absent locally (or
when ``force_refresh=True`` is passed). This means:
  - First run: all files are downloaded from the bucket.
  - Subsequent runs: existing local files are reused (fast restart).
  - Forced refresh: explicitly re-download everything (useful after retraining).

Upload helpers are provided so that training code / CLI scripts can push new
artifacts to the bucket without needing any extra AWS credentials.

Bucket key layout
-----------------
  models/lightgbm_energy_forecaster.joblib
  artifacts/model_config.json
  artifacts/feature_columns.json
  artifacts/metrics.json
  artifacts/feature_importance.csv
  data/energy_consumption_hourly.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.storage import NeonStorageClient

logger = logging.getLogger(__name__)


# Keys inside the bucket (relative paths).
class BucketKeys:
    MODEL = "models/lightgbm_energy_forecaster.joblib"
    MODEL_CONFIG = "artifacts/model_config.json"
    FEATURE_COLUMNS = "artifacts/feature_columns.json"
    METRICS = "artifacts/metrics.json"
    FEATURE_IMPORTANCE = "artifacts/feature_importance.csv"
    HISTORY_CSV = "data/energy_consumption_hourly.csv"


class ArtifactManager:
    """Co-ordinates upload / download of model artifacts with Neon Object Storage.

    Parameters
    ----------
    storage:
        A configured and bucket-ensured :class:`~app.core.storage.NeonStorageClient`.
    local_model_path:
        Local path where the ``.joblib`` model file lives / will be written.
    local_artifacts_dir:
        Directory for the JSON/CSV artifact sidecar files.
    local_history_path:
        Local path for the hourly energy history CSV.
    """

    def __init__(
        self,
        storage: NeonStorageClient,
        local_model_path: Path,
        local_artifacts_dir: Path,
        local_history_path: Path,
    ) -> None:
        self._storage = storage
        self._model_path = Path(local_model_path)
        self._artifacts_dir = Path(local_artifacts_dir)
        self._history_path = Path(local_history_path)

        # Map bucket key → local destination path.
        self._artifact_map: dict[str, Path] = {
            BucketKeys.MODEL: self._model_path,
            BucketKeys.MODEL_CONFIG: self._artifacts_dir / "model_config.json",
            BucketKeys.FEATURE_COLUMNS: self._artifacts_dir / "feature_columns.json",
            BucketKeys.METRICS: self._artifacts_dir / "metrics.json",
            BucketKeys.FEATURE_IMPORTANCE: self._artifacts_dir / "feature_importance.csv",
            BucketKeys.HISTORY_CSV: self._history_path,
        }

    # ---------------------------------------------------------------- download
    def pull_all(self, *, force_refresh: bool = False) -> dict[str, str]:
        """Download all artifacts from the bucket to local disk.

        Files that already exist locally are skipped unless ``force_refresh``
        is ``True``.

        Returns a summary dict  ``{key: "downloaded" | "skipped" | "missing"}``.
        """
        summary: dict[str, str] = {}
        for key, local_path in self._artifact_map.items():
            result = self._pull_one(key, local_path, force_refresh=force_refresh)
            summary[key] = result
        return summary

    def pull_model(self, *, force_refresh: bool = False) -> None:
        """Download only the model + its required sidecar JSONs."""
        required_keys = [
            BucketKeys.MODEL,
            BucketKeys.MODEL_CONFIG,
            BucketKeys.FEATURE_COLUMNS,
        ]
        optional_keys = [BucketKeys.METRICS, BucketKeys.FEATURE_IMPORTANCE]

        for key in required_keys:
            self._pull_one(key, self._artifact_map[key], force_refresh=force_refresh, required=True)

        for key in optional_keys:
            self._pull_one(key, self._artifact_map[key], force_refresh=force_refresh, required=False)

    def pull_history(self, *, force_refresh: bool = False) -> None:
        """Download only the hourly history CSV."""
        self._pull_one(
            BucketKeys.HISTORY_CSV,
            self._history_path,
            force_refresh=force_refresh,
            required=True,
        )

    def _pull_one(
        self,
        key: str,
        local_path: Path,
        *,
        force_refresh: bool,
        required: bool = True,
    ) -> str:
        """Download a single artifact.  Returns "downloaded", "skipped", or "missing"."""
        if local_path.exists() and not force_refresh:
            logger.debug("Artifact already local, skipping: %s", local_path.name)
            return "skipped"

        if not self._storage.object_exists(key):
            msg = f"Artifact not found in Neon bucket: {key}"
            if required:
                raise FileNotFoundError(msg)
            logger.warning("%s (optional — continuing without it)", msg)
            return "missing"

        self._storage.download_file(key, local_path)
        return "downloaded"

    # ------------------------------------------------------------------ upload
    def push_all(self) -> None:
        """Upload all local artifacts to the bucket.

        Only uploads files that exist locally.  Call this after training to
        publish new model artifacts.
        """
        for key, local_path in self._artifact_map.items():
            if local_path.is_file():
                self._storage.upload_file(local_path, key)
            else:
                logger.warning("Skipping upload — local file not found: %s", local_path)

    def push_model(self) -> None:
        """Upload the model joblib + sidecar artifacts (excludes history CSV)."""
        model_keys = [
            BucketKeys.MODEL,
            BucketKeys.MODEL_CONFIG,
            BucketKeys.FEATURE_COLUMNS,
            BucketKeys.METRICS,
            BucketKeys.FEATURE_IMPORTANCE,
        ]
        for key in model_keys:
            local_path = self._artifact_map[key]
            if local_path.is_file():
                self._storage.upload_file(local_path, key)
            else:
                logger.warning("Skipping upload — local file not found: %s", local_path)

    def push_history(self) -> None:
        """Upload the history CSV to the bucket."""
        if self._history_path.is_file():
            self._storage.upload_file(self._history_path, BucketKeys.HISTORY_CSV)
        else:
            logger.warning("Skipping history upload — file not found: %s", self._history_path)

    # -------------------------------------------------------------- properties
    @property
    def storage(self) -> NeonStorageClient:
        return self._storage

    @classmethod
    def from_settings(cls, settings: object) -> "ArtifactManager":
        """Build an ArtifactManager directly from a Settings instance."""
        from app.core.config import get_settings

        s = settings if settings is not None else get_settings()
        storage = NeonStorageClient.from_settings(s)
        storage.ensure_bucket()
        return cls(
            storage=storage,
            local_model_path=s.model_path,
            local_artifacts_dir=s.artifacts_dir,
            local_history_path=s.history_data_path,
        )
