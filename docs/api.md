# API

Base URL (local): `http://localhost:8000` - interactive docs at `/docs`.

**Conventions.** The request `timestamp` is the forecast **origin**: the last observed hour, inclusive, naive
(no timezone), on the hour. A forecast covers origin+1h ... origin+horizon. Only observations at or before the origin
are used. Energy values are `energy_kwh`, unit **kWh**. Timestamps are ISO-8601 without a zone.
Example numbers below are illustrative.

## Errors

`{"detail": "<message>", "error": "<ExceptionName>"}`

| Status | Meaning |
|---|---|
| 422 | Invalid input (schema or domain): bad timestamp/horizon, origin after available history, insufficient contiguous history |
| 503 | Model, hourly history or database unavailable |
| 500 | Artifact/feature mismatch or an unusable prediction |

## Endpoints

### GET /health
`{"status": "ok" | "degraded", "model_loaded": true, "history_loaded": true, "database_ok": true}` - always HTTP 200.

### GET /model-info
`model_name, model_version, dataset, target ("energy_kwh"), unit, frequency ("Hourly"), feature_count, feature_columns, loaded_at, config`.

### POST /predict
Request `{"timestamp": "2026-09-30T10:00:00", "horizon": 24}` (`horizon` 1-168, default 24).

```json
{
  "request_id": "5b0c...",
  "model": "LightGBM",
  "model_version": "v1",
  "horizon": 24,
  "unit": "kWh",
  "forecast_timestamp": "2026-09-30T10:00:00",
  "forecast": [{"timestamp": "2026-09-30T11:00:00", "predicted_energy_kwh": 4.25}]
}
```
Every call is saved to `forecasts` (one row per predicted hour) and logged to `prediction_logs`.

### POST /batch-predict
`{"requests": [{"timestamp": "...", "horizon": 24}, ...]}` (1-10 items). Returns
`{"results": [{"index": 0, "success": true, "result": {...}}, {"index": 1, "success": false, "error": "..."}]}`.
A bad item does not fail the others; a database failure aborts the whole call (503).

### GET /metrics
`{"model_version", "metrics": {...} | null, "feature_importance": [{"feature", "importance"}]}` exactly as exported from
training. `metrics` is `null` if `metrics.json` was not exported.

### GET /forecast-history
Query: `page` (>=1), `page_size` (1-100, default 20), `sort_by` (`created_at` | `prediction_timestamp` |
`predicted_energy_kwh` | `horizon`), `order` (`asc` | `desc`), `date_from`, `date_to` (creation date, inclusive).
Returns `{"items": [{id, forecast_timestamp, prediction_timestamp, predicted_energy_kwh, model_version, horizon, request_id, created_at}], "total", "page", "page_size"}`.

### GET /energy/latest
`{"timestamp", "energy_kwh", "unit"}` - the most recent observed hour (the natural forecast origin).

### GET /energy/history
Query: `hours` (1-8760, default 168), `aggregate` (`hourly` | `daily` | `weekly`), optional `end`.
Returns `{"aggregate", "unit", "points": [{"timestamp", "energy_kwh", "hours"}]}`. Daily/weekly values are **sums** of
hourly kWh; `hours` is the number of hourly observations in the period, so a value below 24 (daily) or 168 (weekly)
marks a partial period. Weeks start on Monday.

## metrics.json contract

Flat lower-case keys for the selected model on the held-out test period - `mae`, `rmse`, `smape`, `r2` - or the same
keys nested under `test`. The UI shows only what is present; nothing is computed or defaulted by the app.
