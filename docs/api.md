# API

Base URL (local): `http://localhost:8000` · Interactive docs: `/docs`

Convention: the request `timestamp` is the **forecast origin** (last observed hour, inclusive, naive, on the hour). Forecast covers origin+1h … origin+horizon. Unit is always kWh.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | `status` ok/degraded, model/history/database flags |
| GET | `/model-info` | Model name/version, features, dataset, target, frequency |
| POST | `/predict` | Body `{timestamp, horizon}`; horizon 1–168 (default 24); saves the forecast |
| POST | `/batch-predict` | Body `{requests: [...]}` (1–10); per-item success/error |
| GET | `/metrics` | Metrics + feature importance exactly as exported from Colab |
| GET | `/forecast-history` | `page`, `page_size`, `sort_by`, `order`, `date_from`, `date_to` |

Errors: 422 invalid input / insufficient history · 503 model, history or database unavailable · 500 internal artifact or computation error. Body: `{"detail": "...", "error": "ExceptionName"}`.
