"""Builds a complete, self-consistent set of TEST artifacts.

The model is a scikit-learn LinearRegression trained on synthetic data using
the production feature pipeline. It exists only to exercise the serving code;
it is not the LightGBM model and its numbers mean nothing.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.services.feature_service import DEFAULT_FEATURE_COLUMNS, build_training_features

START = "2026-01-01 00:00:00"


@dataclass
class TestArtifacts:
    __test__ = False  # not a pytest test class

    root: Path
    model_path: Path
    artifacts_dir: Path
    history_path: Path
    series: pd.Series
    model: LinearRegression


def make_series(n_hours: int = 500, seed: int = 0) -> pd.Series:
    idx = pd.date_range(START, periods=n_hours, freq="h")
    rng = np.random.default_rng(seed)
    values = 10 + 3 * np.sin(2 * np.pi * np.arange(n_hours) / 24) + rng.normal(0, 0.2, n_hours)
    return pd.Series(values, index=idx, name="energy_kwh")


def write_artifacts(root: Path, n_hours: int = 500) -> TestArtifacts:
    root = Path(root)
    (root / "models").mkdir(parents=True, exist_ok=True)
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    series = make_series(n_hours)
    frame = build_training_features(series, DEFAULT_FEATURE_COLUMNS).dropna()
    model = LinearRegression().fit(frame, series.loc[frame.index])

    model_path = root / "models" / "model.joblib"
    joblib.dump(model, model_path)
    (artifacts / "model_config.json").write_text(json.dumps({"model_name": "StandInModel", "model_version": "v-test"}))
    (artifacts / "feature_columns.json").write_text(json.dumps(DEFAULT_FEATURE_COLUMNS))
    (artifacts / "metrics.json").write_text(json.dumps({"note": "synthetic test artifact"}))
    (artifacts / "feature_importance.csv").write_text("feature,importance\nlag_1,1\n")

    history_path = root / "hourly.csv"
    pd.DataFrame({"timestamp": series.index, "energy_kwh_hourly": series.to_numpy()}).to_csv(history_path, index=False)
    return TestArtifacts(root, model_path, artifacts, history_path, series, model)
