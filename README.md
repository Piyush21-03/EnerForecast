# Energy Consumption Forecasting System

End-to-end hourly energy forecasting for the UCI Individual Household Electric Power Consumption data.
Training happens in **Google Colab**; a **FastAPI** service loads the exported model and serves forecasts;
**PostgreSQL** stores forecast history; a **React + Tailwind** dashboard presents everything.
The production backend **never retrains** the model.

## Status

| Part | State |
|---|---|
| Backend (config, DB, model loading, features, forecasting, REST API, tests) | Implemented |
| Frontend (dashboard, forecast, history, model, about) | Implemented |
| Docker Compose (postgres, backend, frontend; optional MLflow) | Implemented |
| **Training notebook** `notebooks/energy_forecasting_training.ipynb` | **Empty stub** - to be written against the real CSV |
| Trained model + artifacts | Not yet produced (see [Model artifacts](#13-model-artifacts)) |

Until the notebook has been run and its artifacts copied in, the API starts but `/health` reports `degraded`
and prediction endpoints return `503`.

## Contents

1. [Project](#1-project) · 2. [Dataset](#2-dataset) · 3. [Dataset columns](#3-dataset-columns) ·
4. [Google Colab workflow](#4-google-colab-workflow) · 5. [Model training](#5-model-training) ·
6. [Model export](#6-model-export) · 7. [Local setup](#7-local-setup) · 8. [PostgreSQL setup](#8-postgresql-setup) ·
9. [Backend setup](#9-backend-setup) · 10. [Frontend setup](#10-frontend-setup) · 11. [Docker](#11-docker) ·
12. [API endpoints](#12-api-endpoints) · 13. [Model artifacts](#13-model-artifacts)

## 1. Project

```
UCI dataset -> Google Colab (clean, EDA, features, train, validate) -> export artifacts
           -> backend/models + backend/artifacts -> FastAPI (features + LightGBM + PostgreSQL)
           -> REST API -> React + Tailwind dashboard
```

See [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md) and [docs/model.md](docs/model.md).

Key rules: chronological splits only (no shuffling), no target leakage, identical feature logic in training and
serving, no invented metrics, and no claim that any algorithm is universally best - the model is
"selected based on the project's validation results".

## 2. Dataset

UCI Individual Household Electric Power Consumption, processed into a CSV of about 2 million rows at
**1-minute** frequency. Timestamp format `YYYY-MM-DD HH:MM:SS`; target `energy_kwh`. The dataset file is not
committed (see `data/README.md`). It is validated in the notebook (row count, duplicates, gaps, missing and invalid
values) before any preprocessing; the app never assumes those checks passed.

## 3. Dataset columns

| Column | Role |
|---|---|
| `timestamp` | Time index |
| `energy_kwh` | **Target** |
| `Global_reactive_power`, `Voltage`, `Global_intensity` | Exogenous (not used as features - see docs/model.md) |
| `Sub_metering_1`, `Sub_metering_2`, `Sub_metering_3` | Exogenous (not used as features) |

Existing column names are used unchanged throughout. There are no `Date`, `Time` or `Global_active_power` columns.

## 4. Google Colab workflow

Open `notebooks/energy_forecasting_training.ipynb` in Colab and upload the CSV. The notebook performs, in order:
validation and missing-data report -> cleaning (no blind gap filling) -> hourly aggregation -> EDA (distribution,
seasonality, rolling statistics, correlation, peaks, ACF/PACF/ADF/KPSS) -> feature engineering -> chronological
train/validation/test split -> expanding-window walk-forward validation -> model comparison -> evaluation -> export.
Feature code must be copied from `backend/app/services/feature_service.py` (`build_training_features`,
`DEFAULT_FEATURE_COLUMNS`) so training and serving cannot drift.

## 5. Model training

- Baselines first: seasonal naive (24 h and 168 h).
- Candidates: Random Forest, XGBoost, LightGBM (primary candidate); ARIMA/SARIMA optional; deep learning only if justified.
- LightGBM hyperparameters are tuned with Optuna (TPE, pruning) using walk-forward validation; nothing is hard-coded beforehand.
- Primary metric MAE; also RMSE, zero-safe MAPE, sMAPE and R^2, plus residual, horizon-wise, peak-period and weekday/weekend analysis.
- The test period stays untouched until model selection is finished.
- Optional experiment tracking: `notebooks/mlflow_utils.py` (see `notebooks/README.md`).

## 6. Model export

At the end of the notebook, write the files listed in [Model artifacts](#13-model-artifacts), download them from
Colab, and copy them into `backend/models/`, `backend/artifacts/` and `data/`. Restart the backend (the model is
loaded once, at startup).

## 7. Local setup

Requirements: Python 3.11+, Node 20+, PostgreSQL 16 (or Docker).

```bash
cp .env.example .env      # then edit; never commit .env
```

Relative paths in `.env` are resolved from the project root.

## 8. PostgreSQL setup

Easiest: run only the database from Compose.

```bash
docker compose up -d postgres
```

Or use your own server and create a role and database matching `DATABASE_URL`:

```sql
CREATE USER energy_user WITH PASSWORD 'change_me';
CREATE DATABASE energy_forecasting OWNER energy_user;
```

Tables (`dataset_metadata`, `model_metadata`, `forecasts`, `prediction_logs`) are created by Alembic migrations.

## 9. Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload          # http://localhost:8000/docs
```

Tests and quality checks:

```bash
pytest --cov
ruff check . && black --check . && mypy app
```

## 10. Frontend setup

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm test
npm run build
```

`VITE_API_BASE_URL` (root `.env`) points the UI at the API; the backend's `CORS_ORIGINS` must include the UI origin.
Commit `package-lock.json` after your first install for reproducible builds.

## 11. Docker

1. `cp .env.example .env` and set a URL-safe `POSTGRES_PASSWORD` (no `@ : / ? #`).
2. Copy the Colab exports into `backend/models/`, `backend/artifacts/` and `data/energy_consumption_hourly.csv`
   (mounted read-only; never baked into images).
3. `docker compose up --build`
4. UI: http://localhost:5173 - API docs: http://localhost:8000/docs
5. Optional MLflow server: `docker compose --profile mlflow up --build` (http://localhost:5000)

The backend runs `alembic upgrade head` on start. `VITE_API_BASE_URL` is baked into the frontend image at build time.

## 12. API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Model / history / database status |
| GET | `/model-info` | Model name, version, features, dataset, target, frequency |
| POST | `/predict` | Forecast 1-168 hours (default 24) from a given origin; saves it |
| POST | `/batch-predict` | Up to 10 forecasts, isolated per item |
| GET | `/metrics` | Exported metrics and feature importance |
| GET | `/forecast-history` | Stored forecasts: pagination, sorting, date filters |
| GET | `/energy/latest` | Latest observed hourly `energy_kwh` |
| GET | `/energy/history` | Observed energy, hourly / daily / weekly |

Details and examples: [docs/api.md](docs/api.md). The request `timestamp` is the forecast **origin** (last observed hour).

## 13. Model artifacts

| File | Location | Contents |
|---|---|---|
| `lightgbm_energy_forecaster.joblib` | `backend/models/` | Fitted estimator (`.predict`) |
| `model_config.json` | `backend/artifacts/` | Object with at least `model_name`, `model_version` |
| `feature_columns.json` | `backend/artifacts/` | List of feature names in training order |
| `metrics.json` | `backend/artifacts/` | Flat `mae`, `rmse`, `smape`, `r2` (or nested under `test`) |
| `feature_importance.csv` | `backend/artifacts/` | Columns `feature`, `importance` |
| `energy_consumption_hourly.csv` | `data/` | Columns `timestamp`, `energy_kwh_hourly` (or `energy_kwh`) - forecast history |

`metrics.json` and `feature_importance.csv` are optional (the UI says so when absent); the first three files
are required. Scalers/imputers are only needed if the notebook uses them; the current feature set needs none.
Only load `.joblib` files you produced yourself (joblib uses pickle).

## Known limitations

- Multi-step forecasts are recursive, so errors can accumulate over long horizons (168 h especially).
- Exogenous columns are not used: their future values are unknown at forecast time.
- The history CSV must be re-exported to include newer observations; the API does not ingest data.
- Timestamps are naive (no timezone handling); origins must be on the hour.
- Weeks in `/energy/history` start on Monday; partial periods are flagged via `hours`.
