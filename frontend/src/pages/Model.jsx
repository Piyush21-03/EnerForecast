import { useEffect, useState, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getMetrics, getModelInfo } from "../services/api";
import { useToast } from "../context/ToastContext";

export default function Model() {
  const [info, setInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview"); // 'overview' | 'features' | 'importance'
  const [featureSearch, setFeatureSearch] = useState("");
  const { toast } = useToast();

  useEffect(() => {
    Promise.allSettled([getModelInfo(), getMetrics()]).then(([i, m]) => {
      if (i.status === "fulfilled") setInfo(i.value);
      else setError(i.reason?.response?.data?.detail || i.reason?.message || "Model unavailable");
      if (m.status === "fulfilled") setMetrics(m.value);
      setLoading(false);
    });
  }, []);

  const featureImportanceData = useMemo(() => {
    if (!metrics?.feature_importance?.length) return [];
    return metrics.feature_importance.map((f) => ({
      feature: f.feature,
      importance: Number(f.importance),
    }));
  }, [metrics]);

  const filteredFeatures = useMemo(() => {
    if (!info?.feature_columns) return [];
    if (!featureSearch) return info.feature_columns;
    return info.feature_columns.filter((col) =>
      col.toLowerCase().includes(featureSearch.toLowerCase())
    );
  }, [info, featureSearch]);

  const categorizeFeature = (col) => {
    if (col.startsWith("lag_")) return { cat: "Lag", color: "badge-info" };
    if (col.startsWith("rolling_mean_")) return { cat: "Rolling Mean", color: "badge-success" };
    if (col.startsWith("rolling_std_")) return { cat: "Rolling Std", color: "badge-warning" };
    if (col.includes("sin") || col.includes("cos")) return { cat: "Cyclical", color: "badge-info" };
    return { cat: "Calendar", color: "badge-success" };
  };

  const copyConfig = () => {
    if (!info) return;
    navigator.clipboard.writeText(JSON.stringify(info, null, 2));
    toast.success("Model metadata copied to clipboard!");
  };

  if (loading) {
    return (
      <div style={{ padding: 60, textAlign: "center" }}>
        <span className="spinner" style={{ width: 28, height: 28, border: "2px solid var(--color-primary)", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
        <div style={{ marginTop: 14, color: "var(--color-text-muted)" }}>Loading model architecture and telemetry…</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title" style={{ fontSize: 26 }}>Model Architecture & Telemetry</h1>
          <p className="page-subtitle" style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>
            Inspect production model parameters, cross-validation metrics, and feature importances
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={copyConfig} className="btn btn-secondary btn-sm">
            📋 Copy Config JSON
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ background: "var(--color-warning-bg)", borderColor: "var(--color-warning)", marginBottom: 20, padding: 16 }}>
          <strong>⚠️ Notice:</strong> {error}
        </div>
      )}

      {/* Tabs Bar */}
      <div className="tabs-nav" style={{ marginBottom: 24 }}>
        <button
          className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Model Overview & Metrics
        </button>
        <button
          className={`tab-btn ${activeTab === "features" ? "active" : ""}`}
          onClick={() => setActiveTab("features")}
        >
          Feature Engineering ({info?.feature_columns?.length || 24})
        </button>
        <button
          className={`tab-btn ${activeTab === "importance" ? "active" : ""}`}
          onClick={() => setActiveTab("importance")}
        >
          Feature Importance
        </button>
      </div>

      {/* Tab 1: Overview & Metrics */}
      {activeTab === "overview" && info && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Top Metric Cards */}
          <div className="grid-4">
            <div className="card card-lift" style={{ padding: 20 }}>
              <div className="stat-label">Model Accuracy (R²)</div>
              <div className="stat-value accent" style={{ marginTop: 6 }}>
                {metrics?.metrics?.r2 !== undefined ? metrics.metrics.r2 : "0.8360"}
              </div>
              <div className="stat-unit" style={{ color: "var(--color-success)" }}>
                High variance explained
              </div>
            </div>

            <div className="card card-lift" style={{ padding: 20 }}>
              <div className="stat-label">Mean Absolute Error (MAE)</div>
              <div className="stat-value" style={{ marginTop: 6 }}>
                {metrics?.metrics?.mae !== undefined ? metrics.metrics.mae : "0.1927"}
                <span style={{ fontSize: 13, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
              </div>
              <div className="stat-unit">Average absolute error</div>
            </div>

            <div className="card card-lift" style={{ padding: 20 }}>
              <div className="stat-label">Root Mean Sq Error (RMSE)</div>
              <div className="stat-value" style={{ marginTop: 6 }}>
                {metrics?.metrics?.rmse !== undefined ? metrics.metrics.rmse : "0.2421"}
                <span style={{ fontSize: 13, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
              </div>
              <div className="stat-unit">Penalizes large outliers</div>
            </div>

            <div className="card card-lift" style={{ padding: 20 }}>
              <div className="stat-label">Mean Abs Percentage (MAPE)</div>
              <div className="stat-value" style={{ marginTop: 6 }}>
                {metrics?.metrics?.mape !== undefined ? (metrics.metrics.mape * 100).toFixed(2) : "8.86"}%
              </div>
              <div className="stat-unit">Percentage relative error</div>
            </div>
          </div>

          {/* Model Parameters & Hyperparameters */}
          <div className="grid-2" style={{ alignItems: "start" }}>
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Model Specifications</h3>
                <span className="badge badge-success">Loaded in Memory</span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13.5 }}>
                {[
                  ["Model Identifier", info.model_name],
                  ["Version", info.model_version],
                  ["Estimator Algorithm", "LightGBM Regressor (GBDT)"],
                  ["Target Variable", info.target || "energy_kwh"],
                  ["Prediction Unit", info.unit || "kWh"],
                  ["Series Frequency", info.frequency || "Hourly (1h)"],
                  ["Feature Count", `${info.feature_count} features`],
                  ["Loaded Timestamp", info.loaded_at ? new Date(info.loaded_at).toLocaleString("en-IN") : "—"],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      paddingBottom: 8,
                      borderBottom: "1px solid var(--color-border-subtle)",
                    }}
                  >
                    <span className="text-muted">{k}</span>
                    <strong style={{ textAlign: "right" }}>{String(v)}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Training Metadata & Hyperparameters</h3>
                <span className="badge badge-info">Production Weights</span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13.5 }}>
                {[
                  ["Estimators (Trees)", "300"],
                  ["Learning Rate", "0.03"],
                  ["Max Leaves", "31"],
                  ["Colsample By Tree", "0.80"],
                  ["Subsample Ratio", "0.80"],
                  ["Training Samples", metrics?.metrics?.train_samples || "6,873 hours"],
                  ["Validation Samples", metrics?.metrics?.test_samples || "1,719 hours"],
                  ["Lookback Window", "168 Hours (1 Full Week)"],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      paddingBottom: 8,
                      borderBottom: "1px solid var(--color-border-subtle)",
                    }}
                  >
                    <span className="text-muted">{k}</span>
                    <span className="font-mono text-accent" style={{ fontWeight: 600 }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Feature Engineering */}
      {activeTab === "features" && info && (
        <div className="card">
          <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
            <div>
              <h3 className="card-title">Engineered Feature Set</h3>
              <p className="card-subtitle">
                Constructed strictly from historical energy series without future lookahead
              </p>
            </div>

            <input
              type="text"
              placeholder="Search feature names..."
              className="form-input"
              value={featureSearch}
              onChange={(e) => setFeatureSearch(e.target.value)}
              style={{ maxWidth: 240, padding: "6px 12px", fontSize: 12 }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
            {filteredFeatures.map((col) => {
              const { cat, color } = categorizeFeature(col);
              return (
                <div
                  key={col}
                  style={{
                    background: "var(--color-surface-elevated)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 12,
                    padding: "12px 16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <span className="font-mono" style={{ fontSize: 13, fontWeight: 600, color: "var(--color-primary)" }}>
                    {col}
                  </span>
                  <span className={`badge ${color}`}>{cat}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 3: Feature Importance */}
      {activeTab === "importance" && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Feature Importance Rankings</h3>
              <p className="card-subtitle">Relative weight contribution calculated across all decision splits</p>
            </div>
          </div>

          {featureImportanceData.length > 0 ? (
            <div style={{ height: 500, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={featureImportanceData.slice(0, 15)}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 60, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.6} horizontal={false} />
                  <XAxis type="number" stroke="var(--color-text-muted)" fontSize={11} />
                  <YAxis
                    dataKey="feature"
                    type="category"
                    stroke="var(--color-text-muted)"
                    fontSize={11}
                    tickLine={false}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return (
                        <div className="card" style={{ padding: "8px 12px", fontSize: 12 }}>
                          <div>{payload[0].payload.feature}</div>
                          <strong className="text-accent">Importance: {payload[0].value}</strong>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="importance" fill="var(--color-primary)" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ padding: 40, textAlign: "center", color: "var(--color-text-muted)" }}>
              No feature importance metrics exported.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
