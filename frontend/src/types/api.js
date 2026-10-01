/**
 * JSDoc typedefs mirroring the backend schemas (docs/api.md).
 * Energy values are `energy_kwh`, unit kWh; timestamps are naive ISO strings.
 */

/** @typedef {{ timestamp: string, predicted_energy_kwh: number }} ForecastPoint */

/**
 * @typedef {Object} PredictResponse
 * @property {string} request_id
 * @property {string} model
 * @property {string} model_version
 * @property {number} horizon
 * @property {string} unit
 * @property {string} forecast_timestamp  Forecast origin (last observed hour)
 * @property {ForecastPoint[]} forecast
 */

/**
 * @typedef {Object} ForecastHistoryItem
 * @property {number} id
 * @property {string} forecast_timestamp
 * @property {string} prediction_timestamp
 * @property {number} predicted_energy_kwh
 * @property {string} model_version
 * @property {number} horizon
 * @property {string} request_id
 * @property {string} created_at
 */

export {};
