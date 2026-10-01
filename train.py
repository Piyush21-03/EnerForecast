"""Model Training & Artifact Generation Pipeline for Energy Consumption Forecasting.

This script can:
1. Accept any input CSV (raw UCI dataset with Date;Time;Global_active_power, or preprocessed hourly CSV).
2. Generate a realistic sample dataset if no CSV is provided yet (using --generate-sample).
3. Process data into hourly energy_kwh.
4. Build training features using the exact feature logic from app.services.feature_service.
5. Train a LightGBM regressor.
6. Evaluate model performance (MAE, RMSE, MAPE, R2).
7. Export all required production artifacts:
   - backend/models/lightgbm_energy_forecaster.joblib
   - backend/artifacts/model_config.json
   - backend/artifacts/feature_columns.json
   - backend/artifacts/metrics.json
   - backend/artifacts/feature_importance.csv
   - data/energy_consumption_hourly.csv
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score

# Ensure backend directory is in sys.path so we can import from app
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.feature_service import DEFAULT_FEATURE_COLUMNS, build_training_features  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train")


def generate_sample_data(hours: int = 8760) -> pd.DataFrame:
    """Generate realistic synthetic hourly energy consumption data for 1 year (8760 hours)."""
    logger.info("Generating %d hours of realistic synthetic energy consumption data...", hours)
    start_date = pd.Timestamp("2024-01-01 00:00:00")
    timestamps = pd.date_range(start=start_date, periods=hours, freq="1h")

    # Base baseline power (kWh)
    base = 1.2

    # Hour of day seasonality (peaks in morning 7-9 AM and evening 6-10 PM)
    hour = timestamps.hour.values
    daily_pattern = (
        0.5 * np.sin(2 * np.pi * (hour - 6) / 24)
        + 0.8 * np.exp(-((hour - 8) ** 2) / 4)
        + 1.5 * np.exp(-((hour - 20) ** 2) / 6)
    )

    # Day of week seasonality (higher usage on weekends)
    dow = timestamps.dayofweek.values
    weekend_factor = np.where(dow >= 5, 0.4, 0.0)

    # Seasonal variation (summer AC and winter heating peaks)
    day_of_year = timestamps.dayofyear.values
    annual_cycle = 0.6 * np.cos(2 * np.pi * (day_of_year - 20) / 365) + 0.4 * np.sin(2 * np.pi * (day_of_year - 200) / 365)

    # Random noise + occasional spikes
    np.random.seed(42)
    noise = np.random.normal(0, 0.2, hours)
    spikes = np.random.exponential(0.1, hours) * np.random.binomial(1, 0.05, hours)

    values = base + daily_pattern + weekend_factor + annual_cycle + noise + spikes
    # Ensure positive kWh values
    values = np.clip(values, 0.1, None)

    return pd.DataFrame({"timestamp": timestamps, "energy_kwh": np.round(values, 4)})


def load_and_preprocess_csv(csv_path: Path) -> pd.DataFrame:
    """Detect delimiter and format of input CSV, then clean and aggregate to hourly energy_kwh."""
    logger.info("Loading input CSV from %s ...", csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    # Sniff delimiter
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(4096)
        delimiter = ";" if ";" in sample and sample.count(";") > sample.count(",") else ","

    df = pd.read_csv(csv_path, sep=delimiter, low_memory=False, na_values=["?", "NaN", "null", ""])
    logger.info("Read %d rows with columns: %s", len(df), list(df.columns))

    # Case 1: UCI Dataset format with Date and Time
    if "Date" in df.columns and "Time" in df.columns:
        logger.info("Detected UCI Household Power Consumption format.")
        # Try both European (DD/MM/YYYY) and ISO (YYYY-MM-DD) date formats
        dt_series = df["Date"].astype(str) + " " + df["Time"].astype(str)
        try:
            df["timestamp"] = pd.to_datetime(dt_series, format="%d/%m/%Y %H:%M:%S")
        except ValueError:
            df["timestamp"] = pd.to_datetime(dt_series)

        # Global_active_power is in kilowatt. Hourly mean kW is equivalent to hourly kWh.
        target_col = "Global_active_power"
        if target_col not in df.columns:
            for c in df.columns:
                if "active_power" in c.lower() or "power" in c.lower() or "energy" in c.lower():
                    target_col = c
                    break

        df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
        df = df.dropna(subset=["timestamp", target_col])
        df = df.set_index("timestamp").sort_index()

        # Resample to hourly mean (kW averaged over 1 hour = kWh)
        hourly_series = df[target_col].resample("1h").mean()
        # Interpolate short missing gaps
        hourly_series = hourly_series.interpolate(method="time", limit=6).dropna()

        result = pd.DataFrame({
            "timestamp": hourly_series.index,
            "energy_kwh": hourly_series.values
        })
        return result

    # Case 2: Standard CSV with timestamp or date/datetime column
    ts_col = None
    for c in df.columns:
        if c.lower() in ("timestamp", "datetime", "date", "time"):
            ts_col = c
            break

    if ts_col is None:
        raise ValueError(f"Could not find timestamp/date column in CSV. Found: {list(df.columns)}")

    target_col = None
    for c in df.columns:
        if c.lower() in ("energy_kwh", "energy", "kwh", "consumption", "power", "load", "value"):
            target_col = c
            break

    if target_col is None:
        numeric_cols = [c for c in df.columns if c != ts_col and pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            target_col = numeric_cols[0]
        else:
            raise ValueError(f"Could not find energy target column in CSV. Columns: {list(df.columns)}")

    logger.info("Using timestamp column '%s' and target column '%s'", ts_col, target_col)
    df["timestamp"] = pd.to_datetime(df[ts_col])
    if df["timestamp"].dt.tz is not None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    df["energy_kwh"] = pd.to_numeric(df[target_col], errors="coerce")
    df = df.dropna(subset=["timestamp", "energy_kwh"])
    df = df.set_index("timestamp").sort_index()

    # If already hourly, ensure regular grid
    hourly_series = df["energy_kwh"].resample("1h").mean()
    hourly_series = hourly_series.interpolate(method="time", limit=6).dropna()

    return pd.DataFrame({"timestamp": hourly_series.index, "energy_kwh": hourly_series.values})


def train_model(
    data_df: pd.DataFrame,
    model_name: str = "lightgbm_energy_forecaster",
    model_version: str = "1.0.0",
    test_ratio: float = 0.2,
):
    """Build features, train LightGBM regressor, compute metrics, and export artifacts."""
    logger.info("Preparing data series for feature engineering...")
    data_df = data_df.drop_duplicates(subset=["timestamp"], keep="first").sort_values("timestamp")
    series = pd.Series(
        data_df["energy_kwh"].astype(float).values,
        index=pd.DatetimeIndex(data_df["timestamp"].values),
        name="energy_kwh",
    )

    logger.info("Building features using %d feature columns...", len(DEFAULT_FEATURE_COLUMNS))
    X = build_training_features(series, DEFAULT_FEATURE_COLUMNS)
    y = series.loc[X.index]

    # Drop initial rows with NaN from lags/rolling windows
    valid_mask = ~(X.isna().any(axis=1) | y.isna())
    X = X[valid_mask]
    y = y[valid_mask]

    n_samples = len(X)
    logger.info("Feature engineering complete: %d valid samples with %d features.", n_samples, X.shape[1])
    if n_samples < 200:
        raise ValueError(f"Too few valid samples ({n_samples}) for training. Need at least 200 hours of history.")

    # Time-series split (preserve temporal ordering)
    split_idx = int(n_samples * (1 - test_ratio))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    logger.info("Training set: %d samples (%s to %s)", len(X_train), X_train.index[0], X_train.index[-1])
    logger.info("Testing set:  %d samples (%s to %s)", len(X_test), X_test.index[0], X_test.index[-1])

    # Train LightGBM model
    logger.info("Training LightGBM Regressor...")
    model = LGBMRegressor(
        n_estimators=1500,
        learning_rate=0.01,
        num_leaves=127,
        max_depth=10,
        min_child_samples=15,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=2.0,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    # Predict & evaluate
    logger.info("Evaluating model on test set...")
    y_pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    # Avoid zero division in MAPE
    nonzero_mask = y_test > 1e-4
    mape = float(mean_absolute_percentage_error(y_test[nonzero_mask], y_pred[nonzero_mask])) if nonzero_mask.any() else 0.0
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
        "r2": round(r2, 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_period": {
            "start": str(X_test.index[0]),
            "end": str(X_test.index[-1]),
        },
    }

    logger.info("Evaluation Results:")
    logger.info("  MAE:  %.4f kWh", metrics["mae"])
    logger.info("  RMSE: %.4f kWh", metrics["rmse"])
    logger.info("  MAPE: %.2f%%", metrics["mape"] * 100)
    logger.info("  R²:   %.4f", metrics["r2"])

    # Feature Importance
    importances = model.feature_importances_
    feat_imp = [
        {"feature": col, "importance": float(imp)}
        for col, imp in zip(DEFAULT_FEATURE_COLUMNS, importances)
    ]
    feat_imp.sort(key=lambda x: x["importance"], reverse=True)

    # Export paths
    models_dir = BACKEND_DIR / "models"
    artifacts_dir = BACKEND_DIR / "artifacts"
    data_dir = REPO_ROOT / "data"

    models_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    model_file = models_dir / "lightgbm_energy_forecaster.joblib"
    config_file = artifacts_dir / "model_config.json"
    features_file = artifacts_dir / "feature_columns.json"
    metrics_file = artifacts_dir / "metrics.json"
    importance_file = artifacts_dir / "feature_importance.csv"
    history_file = data_dir / "energy_consumption_hourly.csv"

    # Save model
    logger.info("Saving model to %s", model_file)
    joblib.dump(model, model_file)

    # Save model config
    config = {
        "model_name": model_name,
        "model_version": model_version,
        "algorithm": "LightGBM Regressor",
        "target": "energy_kwh",
        "unit": "kWh",
        "frequency": "hourly",
        "features_count": len(DEFAULT_FEATURE_COLUMNS),
        "training_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "hyperparameters": {
            "n_estimators": 1500,
            "learning_rate": 0.01,
            "num_leaves": 127,
            "max_depth": 10,
            "min_child_samples": 15,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 2.0,
        },
    }
    logger.info("Saving model config to %s", config_file)
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # Save feature columns
    logger.info("Saving feature columns to %s", features_file)
    features_file.write_text(json.dumps(DEFAULT_FEATURE_COLUMNS, indent=2), encoding="utf-8")

    # Save metrics
    logger.info("Saving metrics to %s", metrics_file)
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Save feature importance CSV
    logger.info("Saving feature importance to %s", importance_file)
    with importance_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["feature", "importance"])
        writer.writeheader()
        writer.writerows(feat_imp)

    # Save hourly history CSV
    logger.info("Saving hourly history dataset (%d rows) to %s", len(data_df), history_file)
    data_df.to_csv(history_file, index=False)

    logger.info("All artifacts successfully created and saved!")
    return {
        "model_path": str(model_file),
        "config_path": str(config_file),
        "features_path": str(features_file),
        "metrics_path": str(metrics_file),
        "importance_path": str(importance_file),
        "history_path": str(history_file),
        "metrics": metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Train Energy Forecasting Model and Export Artifacts")
    parser.add_argument("--csv", type=str, default=None, help="Path to input dataset CSV")
    parser.add_argument("--generate-sample", action="store_true", help="Generate realistic 1-year sample dataset")
    parser.add_argument("--model-version", type=str, default="1.0.0", help="Model version string")
    args = parser.parse_args()

    csv_path = None
    if args.csv:
        csv_path = Path(args.csv)
    elif (REPO_ROOT / "data" / "energy_consumption.csv").exists():
        csv_path = REPO_ROOT / "data" / "energy_consumption.csv"
    elif (REPO_ROOT / "data" / "household_power_consumption.txt").exists():
        csv_path = REPO_ROOT / "data" / "household_power_consumption.txt"

    if csv_path and csv_path.exists() and not args.generate_sample:
        logger.info("Using existing dataset: %s", csv_path)
        data_df = load_and_preprocess_csv(csv_path)
    else:
        logger.info("No CSV specified or found in data/. Generating realistic 1-year sample dataset...")
        data_df = generate_sample_data(hours=8760)

    train_model(data_df, model_version=args.model_version)


if __name__ == "__main__":
    main()
