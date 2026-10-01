# Architecture

```
                UCI DATASET
                     |
                     v
               GOOGLE COLAB   (validation, cleaning, EDA, features, training, evaluation)
                     |
                     v  export .joblib + JSON/CSV artifacts
             LOCAL PROJECT / DOCKER VOLUMES
                     |
                     v
                  FastAPI
      +--------------+---------------+
      v              v               v
  FeatureService  ModelService   PostgreSQL
      +--------------+---------------+
                     v
                  REST API
                     v
             React + Tailwind (Vite, Recharts)
```

Training and inference are strictly separate. The backend contains no training code and its runtime
requirements exclude training libraries (enforced by `tests/test_packaging.py`).

## Backend layers (`backend/app`)

| Layer | Files | Responsibility |
|---|---|---|
| API | `api/routes/*`, `api/deps.py`, `api/errors.py` | HTTP, validation (Pydantic), exception -> status mapping |
| Services | `model_service`, `feature_service`, `forecast_service`, `history_provider`, `analytics_service` | Model loading/inference, features, recursive forecasting, history access, aggregation |
| Repositories | `forecast_repository`, `model_repository` | All SQLAlchemy access |
| Core / DB | `core/config`, `core/logging`, `core/exceptions`, `db/database`, `models/*` | Settings, logging, domain errors, engine/session, ORM + schemas |

Services do not import SQLAlchemy at module level (the repository is injected), so forecasting logic is testable without a database.

## Startup (`main.py` lifespan)

1. Load settings (env / `.env`); configure logging and CORS; register routers and error handlers.
2. `ModelService.load()` - model, `model_config.json`, `feature_columns.json`, optional metrics/importance. Validates the model's stored feature names against `feature_columns.json`.
3. `CsvHistoryProvider` loads the hourly history once.
4. `FeatureService(feature_columns)` and `ForecastService` are built (they refuse to start if the feature lists differ).
5. Best-effort: record model and dataset metadata in PostgreSQL.

Any failure in 2-4 is logged and the app still starts; `/health` reports `degraded` and dependent endpoints return 503.

## Forecast request flow (`POST /predict`)

1. Pydantic validates `{timestamp, horizon}`; the service checks hour alignment, naive timestamp and history availability.
2. The last `required_lookback_hours` (168 for the default feature set) ending at the origin are taken from history.
3. For each step t+1 ... t+h: build one feature row from history plus earlier predictions, call the model, append the prediction to the working history (recursive forecasting). Real observations after the origin are never used.
4. Save one `forecasts` row per predicted hour and one `prediction_logs` row (success or error).
5. Return the structured response.

## Feature parity

`feature_service.py` is the single source of truth: `FeatureService.build_row` (serving) and `build_training_features` (vectorised, for the notebook) implement identical definitions, verified by a parity test. Rolling features always use the target shifted by one hour; missing history raises an error instead of being filled.

## Database

| Table | Purpose |
|---|---|
| `dataset_metadata` | Dataset served by this instance (rows, range, frequency), written at startup |
| `model_metadata` | Model versions seen; exactly one active |
| `forecasts` | One row per predicted hour: origin, predicted timestamp, kWh, model version, horizon, request id, created_at |
| `prediction_logs` | Per request: endpoint, payload, status, error, latency, model version |

Schema is managed by Alembic (`app/db/migrations`); a test checks the migration matches the ORM models.

## Frontend (`frontend/src`)

Routes: Dashboard, Forecast, History, Model, About. `services/api.js` (Axios) -> `hooks/useAsync.js` -> pages. Charts use Recharts through `components/charts`. Each chart and table handles loading, error and empty states. Forecasts are generated only on user action because every call is stored.

## Deployment

`docker-compose.yml`: `postgres` (health-checked, persistent volume) -> `backend` (migrates, then serves; artifacts mounted read-only) -> `frontend` (nginx, SPA fallback). Optional `mlflow` profile for experiment tracking. Frontend and backend are independently deployable; the only coupling is `VITE_API_BASE_URL` (build time) and `CORS_ORIGINS` (runtime).

## Security

Secrets only via environment (`.env` is git-ignored; `.env.example` holds placeholders); Pydantic validation on all input; SQLAlchemy parameterised queries with a whitelist for sort columns; explicit CORS origins; non-root backend container; Postgres and MLflow published on localhost only; `.joblib` files must be self-produced (pickle).
