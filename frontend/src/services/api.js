import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Health
export const getHealth = () => client.get("/health").then((r) => r.data);

// Forecast
export const predict = (timestamp, horizon) =>
  client.post("/predict", { timestamp, horizon }).then((r) => r.data);

export const batchPredict = (requests) =>
  client.post("/batch-predict", { requests }).then((r) => r.data);

// Model
export const getModelInfo = () => client.get("/model-info").then((r) => r.data);
export const getMetrics = () => client.get("/metrics").then((r) => r.data);

// History
export const getForecastHistory = (params) =>
  client.get("/forecast-history", { params }).then((r) => r.data);

// Energy
export const getLatestEnergy = () =>
  client.get("/energy/latest").then((r) => r.data);

export const getEnergyHistory = (aggregate = "daily", limit = 90) =>
  client.get("/energy/history", { params: { aggregate, limit } }).then((r) => r.data);

export default client;
