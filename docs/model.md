# Model

Selected based on the project's validation results. No ranking of algorithms is implied, and no metric appears in this
document until it has been produced by the training notebook and exported in `metrics.json`.

## Problem

Forecast hourly household `energy_kwh` for the next 24 h (primary) and up to 168 h, from history only.

## Data and aggregation

Source: 1-minute UCI-derived CSV (`timestamp`, `energy_kwh`, `Global_reactive_power`, `Voltage`, `Global_intensity`, `Sub_metering_1-3`).
The notebook first validates the data (row count, dtypes, duplicate/missing timestamps, missing and invalid values, ordering, 1-minute frequency) and writes a missing-data report. Short gaps may be interpolated (documented); long gaps stay missing and affected training windows are excluded.

**Hourly aggregation must follow what `energy_kwh` means**, so the notebook inspects the column's semantics before choosing:
- per-minute energy (kWh in each minute) -> hourly **sum**;
- average power (kW) -> hourly **mean**, and the notebook states how the hourly value relates to kWh.

`valid_minute_share = valid_minutes / expected_minutes` is stored per hour, and hours below a documented threshold are treated as missing. The application assumes the hourly target is kWh per hour, which is why its daily/weekly values are sums. Other columns are aggregated per their meaning (e.g. voltage/intensity/reactive power as means, sub-metering as sums) and each choice is documented in the notebook.

## Features (production set)

Defined once in `backend/app/services/feature_service.py` (`DEFAULT_FEATURE_COLUMNS`); `feature_columns.json` records the order used at training.

| Group | Features |
|---|---|
| Lags | `lag_1, lag_2, lag_3, lag_24, lag_48, lag_168` (optional `lag_336`, `lag_8760` if justified) |
| Rolling mean / std | windows 3, 6, 24, 168 over the target **shifted by 1 hour** (sample std, ddof=1) |
| Calendar | `hour, day_of_month, day_of_week` (Mon=0), `month, week_of_year` (ISO), `is_weekend` |
| Cyclical | `hour_sin/cos` (period 24), `day_of_week_sin/cos` (period 7) |

Exogenous columns are excluded: their future values are unavailable at forecast time. If added later they must enter as lagged values only.

## Validation

- Chronological train / validation / test; no shuffling, no random `train_test_split`; the test period is untouched until selection is complete.
- Expanding-window walk-forward validation over many origins: 24 h horizon (primary), 168 h (extension).

## Models

Baselines: seasonal naive 24 h and 168 h. Candidates: Random Forest, XGBoost, LightGBM (primary candidate); ARIMA/SARIMA optional; LSTM/GRU only if justified. LightGBM is tuned with Optuna (TPE + pruning) over `num_leaves, learning_rate, n_estimators, max_depth, min_child_samples, subsample, colsample_bytree, reg_lambda, reg_alpha`; no optimal values are assumed in advance.

## Evaluation

Primary MAE; also RMSE, MAPE (zero-safe), sMAPE, R^2. Analyses: error distribution, residuals, actual vs predicted, horizon-wise error, peak-period error, weekday/weekend performance.

## Export contract

| Artifact | Requirement |
|---|---|
| `lightgbm_energy_forecaster.joblib` | Fitted estimator whose stored feature names equal `feature_columns.json` |
| `model_config.json` | Object with `model_name`, `model_version` (extra keys are passed to `/model-info`) |
| `feature_columns.json` | Unique names, in training order |
| `metrics.json` | Flat `mae, rmse, smape, r2` (or under `test`) for the held-out test period |
| `feature_importance.csv` | `feature, importance` |
| `energy_consumption_hourly.csv` | `timestamp`, `energy_kwh_hourly`; hour-aligned, unique, ascending |

The backend refuses to load a model whose feature names or order differ from `feature_columns.json`.

## Inference behaviour and limits

Recursive multi-step forecasting: each predicted hour becomes a lag for the next, so error can accumulate, especially at 168 h. Origins need 168 contiguous prior hours (for the default features); gaps produce a clear 422 error rather than silent filling. Predictions are not clipped or post-processed. The app never retrains.
