import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from app.core.exceptions import (
    ArtifactNotFoundError,
    FeatureMismatchError,
    InvalidArtifactError,
    ModelNotLoadedError,
)
from app.services.model_service import ModelService

FEATURES = ["lag_1", "lag_24", "hour_sin"]


def make_service(d) -> ModelService:
    return ModelService(
        model_path=d / "models" / "model.joblib",
        model_config_path=d / "artifacts" / "model_config.json",
        feature_columns_path=d / "artifacts" / "feature_columns.json",
        metrics_path=d / "artifacts" / "metrics.json",
        feature_importance_path=d / "artifacts" / "feature_importance.csv",
    )


@pytest.fixture
def artifacts(tmp_path):
    """Synthetic artifacts. A scikit-learn stand-in model is used only to test
    loading/validation logic; it is NOT the trained LightGBM model."""
    (tmp_path / "models").mkdir()
    (tmp_path / "artifacts").mkdir()
    X = pd.DataFrame(np.arange(30, dtype=float).reshape(10, 3), columns=FEATURES)
    y = X["lag_1"] * 2
    joblib.dump(LinearRegression().fit(X, y), tmp_path / "models" / "model.joblib")
    a = tmp_path / "artifacts"
    (a / "model_config.json").write_text(json.dumps({"model_name": "TestModel", "model_version": "v-test"}))
    (a / "feature_columns.json").write_text(json.dumps(FEATURES))
    (a / "metrics.json").write_text(json.dumps({"mae": 1.0}))
    (a / "feature_importance.csv").write_text("feature,importance\nlag_1,10\n")
    return tmp_path


def loaded(artifacts) -> ModelService:
    svc = make_service(artifacts)
    svc.load()
    return svc


def test_load_and_metadata(artifacts):
    svc = loaded(artifacts)
    assert svc.is_loaded
    assert svc.model_version == "v-test"
    info = svc.get_model_info()
    assert info["feature_count"] == 3 and info["model_name"] == "TestModel"
    assert svc.get_metrics() == {"mae": 1.0}
    assert svc.get_feature_importance() == [{"feature": "lag_1", "importance": "10"}]


def test_predict_returns_one_value_per_row(artifacts):
    svc = loaded(artifacts)
    X = pd.DataFrame([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], columns=FEATURES)
    preds = svc.predict(X)
    assert preds.shape == (2,)
    assert preds[0] == pytest.approx(2.0)


def test_missing_model_file(artifacts):
    (artifacts / "models" / "model.joblib").unlink()
    with pytest.raises(ArtifactNotFoundError):
        make_service(artifacts).load()


def test_missing_optional_artifacts_are_tolerated(artifacts):
    (artifacts / "artifacts" / "metrics.json").unlink()
    (artifacts / "artifacts" / "feature_importance.csv").unlink()
    svc = loaded(artifacts)
    assert svc.get_metrics() is None
    assert svc.get_feature_importance() == []


def test_invalid_config_and_columns(artifacts):
    (artifacts / "artifacts" / "model_config.json").write_text(json.dumps({"model_name": "x"}))
    with pytest.raises(InvalidArtifactError):
        make_service(artifacts).load()
    (artifacts / "artifacts" / "model_config.json").write_text(json.dumps({"model_name": "x", "model_version": "1"}))
    (artifacts / "artifacts" / "feature_columns.json").write_text("not json")
    with pytest.raises(InvalidArtifactError):
        make_service(artifacts).load()


def test_corrupt_model_file(artifacts):
    (artifacts / "models" / "model.joblib").write_bytes(b"garbage")
    with pytest.raises(InvalidArtifactError):
        make_service(artifacts).load()


def test_model_vs_feature_columns_mismatch_at_load(artifacts):
    (artifacts / "artifacts" / "feature_columns.json").write_text(json.dumps(["lag_24", "lag_1", "hour_sin"]))
    with pytest.raises(FeatureMismatchError):
        make_service(artifacts).load()


def test_predict_rejects_wrong_order_missing_and_extra(artifacts):
    svc = loaded(artifacts)
    row = [[1.0, 2.0, 3.0]]
    with pytest.raises(FeatureMismatchError, match="different order"):
        svc.predict(pd.DataFrame(row, columns=["lag_24", "lag_1", "hour_sin"]))
    with pytest.raises(FeatureMismatchError, match="Missing"):
        svc.predict(pd.DataFrame([[1.0, 2.0]], columns=["lag_1", "lag_24"]))
    with pytest.raises(FeatureMismatchError, match="Unexpected"):
        svc.predict(pd.DataFrame([[1.0, 2.0, 3.0, 4.0]], columns=FEATURES + ["extra"]))


def test_predict_empty_frame_rejected(artifacts):
    with pytest.raises(FeatureMismatchError):
        loaded(artifacts).predict(pd.DataFrame(columns=FEATURES))


def test_not_loaded_errors(artifacts):
    svc = make_service(artifacts)
    assert not svc.is_loaded
    with pytest.raises(ModelNotLoadedError):
        svc.predict(pd.DataFrame([[1.0, 2.0, 3.0]], columns=FEATURES))
    with pytest.raises(ModelNotLoadedError):
        svc.get_model_info()


def test_real_lightgbm_model_round_trip(artifacts):
    lgb = pytest.importorskip("lightgbm")
    X = pd.DataFrame(np.random.default_rng(0).random((50, 3)), columns=FEATURES)
    y = X["lag_1"] * 3
    joblib.dump(lgb.LGBMRegressor(n_estimators=5, verbose=-1).fit(X, y), artifacts / "models" / "model.joblib")
    svc = loaded(artifacts)
    assert svc.predict(X.head(3)).shape == (3,)
