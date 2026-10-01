import { useState, useEffect, useMemo } from "react";
import {
  Area,
  AreaChart,
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { getLatestEnergy, predict } from "../services/api";
import { useToast } from "../context/ToastContext";
import EmptyState from "../components/EmptyState";

function formatTimestamp(ts) {
  return new Date(ts).toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function CustomForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border-hover)",
        borderRadius: 12,
        padding: "10px 14px",
        boxShadow: "var(--shadow-md)",
      }}
    >
      <div style={{ fontSize: 11.5, color: "var(--color-text-muted)", marginBottom: 4 }}>
        {formatTimestamp(label)}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span style={{ fontSize: 18, fontWeight: 800, color: "var(--color-primary)" }}>
          {Number(payload[0].value).toFixed(3)}
        </span>
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>kWh</span>
      </div>
    </div>
  );
}

export default function Forecast() {
  const [timestamp, setTimestamp] = useState("");
  const [latestTs, setLatestTs] = useState("");
  const [horizon, setHorizon] = useState(24);
  const [chartType, setChartType] = useState("area"); // 'area' | 'line'
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [tablePage, setTablePage] = useState(1);
  const pageSize = 10;
  const { toast } = useToast();

  // Load latest available energy timestamp on mount
  useEffect(() => {
    getLatestEnergy()
      .then((data) => {
        if (data?.timestamp) {
          const d = new Date(data.timestamp);
          const pad = (n) => String(n).padStart(2, "0");
          const formatted = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
          setTimestamp(formatted);
          setLatestTs(formatted);
        }
      })
      .catch(() => {
        const now = new Date();
        now.setMinutes(0, 0, 0);
        const pad = (n) => String(n).padStart(2, "0");
        const formatted = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:00`;
        setTimestamp(formatted);
      });
  }, []);

  const handleUseLatest = () => {
    if (latestTs) {
      setTimestamp(latestTs);
      toast.info("Set timestamp to latest recorded observation in history.");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await predict(timestamp, Number(horizon));
      setResult(data);
      toast.success(`Generated ${data.forecast?.length || horizon}h energy forecast successfully!`);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Failed to generate prediction";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const chartPoints = useMemo(() => {
    if (!result?.forecast) return [];
    return result.forecast.map((p) => ({
      timestamp: p.timestamp,
      predicted_energy_kwh: Number(Number(p.predicted_energy_kwh).toFixed(3)),
    }));
  }, [result]);

  const stats = useMemo(() => {
    if (!chartPoints.length) return null;
    const values = chartPoints.map((p) => p.predicted_energy_kwh);
    const sum = values.reduce((a, b) => a + b, 0);
    return {
      total: sum,
      avg: sum / values.length,
      peak: Math.max(...values),
      min: Math.min(...values),
    };
  }, [chartPoints]);

  const filteredPoints = useMemo(() => {
    if (!searchTerm) return chartPoints;
    return chartPoints.filter((p) =>
      p.timestamp.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [chartPoints, searchTerm]);

  const paginatedPoints = useMemo(() => {
    const start = (tablePage - 1) * pageSize;
    return filteredPoints.slice(start, start + pageSize);
  }, [filteredPoints, tablePage]);

  const totalTablePages = Math.ceil(filteredPoints.length / pageSize) || 1;

  const exportCsv = () => {
    if (!chartPoints.length) return;
    const headers = "timestamp,predicted_energy_kwh,unit\n";
    const rows = chartPoints.map((p) => `${p.timestamp},${p.predicted_energy_kwh},kWh`).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `forecast_${result?.request_id || "export"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Downloaded forecast CSV file.");
  };

  const copyJson = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    toast.success("Forecast JSON copied to clipboard!");
  };

  return (
    <div className="fade-in">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title" style={{ fontSize: 26 }}>Energy Demand Forecasting</h1>
          <p className="page-subtitle" style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>
            Execute multi-step recursive autoregressive forecasts powered by LightGBM
          </p>
        </div>

        {result && (
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={copyJson} className="btn btn-secondary btn-sm">
              <span>📋 Copy JSON</span>
            </button>
            <button onClick={exportCsv} className="btn btn-primary btn-sm">
              <span>📥 Export CSV</span>
            </button>
          </div>
        )}
      </div>

      <div className="grid-1-2" style={{ alignItems: "start" }}>
        {/* Parameters Form Card */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Forecast Parameters</h3>
              <p className="card-subtitle">Configure origin timestamp & horizon window</p>
            </div>
            <span className="badge badge-info">Autoregressive</span>
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Origin Timestamp */}
            <div className="form-group">
              <label className="form-label" htmlFor="forecast-origin">
                <span>Forecast Origin</span>
                {latestTs && (
                  <button
                    type="button"
                    onClick={handleUseLatest}
                    style={{
                      background: "transparent",
                      color: "var(--color-primary)",
                      fontSize: 11,
                      fontWeight: 600,
                      textDecoration: "underline",
                      cursor: "pointer",
                      border: "none",
                      padding: 0,
                    }}
                  >
                    ⚡ Use Latest Available ({latestTs.slice(0, 10)})
                  </button>
                )}
              </label>
              <input
                id="forecast-origin"
                type="datetime-local"
                className="form-input"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                required
              />
              <span style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
                Model uses observations strictly at or prior to this hour.
              </span>
            </div>

            {/* Horizon Presets */}
            <div className="form-group">
              <label className="form-label">
                <span>Forecast Horizon: {horizon} Hours</span>
                <span style={{ color: "var(--color-primary)", fontWeight: 700 }}>
                  ({(horizon / 24).toFixed(1)} Days)
                </span>
              </label>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
                {[6, 12, 24, 48, 72, 168].map((h) => (
                  <button
                    key={h}
                    type="button"
                    className={`preset-chip ${horizon === h ? "active" : ""}`}
                    onClick={() => setHorizon(h)}
                  >
                    {h === 24 ? "24h (1 Day)" : h === 48 ? "48h (2 Days)" : h === 168 ? "168h (1 Wk)" : `${h}h`}
                  </button>
                ))}
              </div>

              <input
                type="range"
                min={1}
                max={168}
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                style={{ width: "100%", accentColor: "var(--color-primary)" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--color-text-muted)" }}>
                <span>1 Hour</span>
                <span>168 Hours (7 Days)</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: "100%", padding: "12px", fontSize: 14 }}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 16, height: 16, border: "2px solid #fff", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                  <span>Computing Dynamic Features…</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>Generate Multi-Step Forecast</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div
              style={{
                marginTop: 20,
                padding: "14px 16px",
                borderRadius: 12,
                background: "var(--color-danger-bg)",
                border: "1px solid var(--color-danger)",
                color: "var(--color-danger)",
                fontSize: 13,
                lineHeight: 1.5,
              }}
            >
              <strong>⚠️ Forecasting Error:</strong>
              <div style={{ marginTop: 4 }}>{error}</div>
              {error.includes("last available history") && (
                <button
                  onClick={handleUseLatest}
                  className="btn btn-secondary btn-sm"
                  style={{ marginTop: 10, width: "100%" }}
                >
                  ⚡ Auto-fill with Latest History Timestamp
                </button>
              )}
            </div>
          )}
        </div>

        {/* Results & Visualisation Area */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {result ? (
            <>
              {/* Summary Metric Pills */}
              <div className="grid-4" style={{ gap: 14 }}>
                <div className="card" style={{ padding: 16 }}>
                  <div className="stat-label">Total Projected</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: "var(--color-primary)", marginTop: 4 }}>
                    {stats?.total.toFixed(2)}
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
                  </div>
                </div>

                <div className="card" style={{ padding: 16 }}>
                  <div className="stat-label">Average Load</div>
                  <div style={{ fontSize: 20, fontWeight: 800, marginTop: 4 }}>
                    {stats?.avg.toFixed(3)}
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
                  </div>
                </div>

                <div className="card" style={{ padding: 16 }}>
                  <div className="stat-label">Peak Demand</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: "var(--color-danger)", marginTop: 4 }}>
                    {stats?.peak.toFixed(3)}
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
                  </div>
                </div>

                <div className="card" style={{ padding: 16 }}>
                  <div className="stat-label">Min Demand</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: "var(--color-success)", marginTop: 4 }}>
                    {stats?.min.toFixed(3)}
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
                  </div>
                </div>
              </div>

              {/* Main Interactive Forecast Chart */}
              <div className="card card-lift">
                <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
                  <div>
                    <h3 className="card-title">Forecast Trajectory</h3>
                    <p className="card-subtitle">
                      Origin: {formatTimestamp(result.forecast_timestamp)} | Model: {result.model_version}
                    </p>
                  </div>

                  <div className="tabs-nav">
                    <button
                      className={`tab-btn ${chartType === "area" ? "active" : ""}`}
                      onClick={() => setChartType("area")}
                    >
                      Area Chart
                    </button>
                    <button
                      className={`tab-btn ${chartType === "line" ? "active" : ""}`}
                      onClick={() => setChartType("line")}
                    >
                      Line Chart
                    </button>
                  </div>
                </div>

                <div style={{ height: 320, width: "100%" }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {chartType === "area" ? (
                      <AreaChart data={chartPoints} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <defs>
                          <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.6} />
                        <XAxis
                          dataKey="timestamp"
                          tickFormatter={(t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          stroke="var(--color-text-muted)"
                          fontSize={11}
                          tickLine={false}
                        />
                        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} unit=" kWh" />
                        <Tooltip content={<CustomForecastTooltip />} />
                        <ReferenceLine
                          y={stats?.avg}
                          stroke="var(--color-accent)"
                          strokeDasharray="4 4"
                          label={{ value: `Avg ${stats?.avg.toFixed(2)}`, fill: "var(--color-text-secondary)", fontSize: 10 }}
                        />
                        <Area
                          type="monotone"
                          dataKey="predicted_energy_kwh"
                          stroke="var(--color-primary)"
                          strokeWidth={2.5}
                          fill="url(#forecastFill)"
                          activeDot={{ r: 6, fill: "var(--color-primary)", stroke: "var(--color-surface)", strokeWidth: 2 }}
                        />
                      </AreaChart>
                    ) : (
                      <LineChart data={chartPoints} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.6} />
                        <XAxis
                          dataKey="timestamp"
                          tickFormatter={(t) => new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          stroke="var(--color-text-muted)"
                          fontSize={11}
                          tickLine={false}
                        />
                        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} unit=" kWh" />
                        <Tooltip content={<CustomForecastTooltip />} />
                        <ReferenceLine
                          y={stats?.avg}
                          stroke="var(--color-accent)"
                          strokeDasharray="4 4"
                          label={{ value: `Avg ${stats?.avg.toFixed(2)}`, fill: "var(--color-text-secondary)", fontSize: 10 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="predicted_energy_kwh"
                          stroke="var(--color-primary)"
                          strokeWidth={2.5}
                          dot={{ r: 3, fill: "var(--color-primary)" }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Data Points Table */}
              <div className="card">
                <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
                  <div>
                    <h3 className="card-title">Hourly Predictions Breakdown</h3>
                    <p className="card-subtitle">Showing {filteredPoints.length} sequential forecast points</p>
                  </div>

                  <input
                    type="text"
                    placeholder="Search timestamp..."
                    className="form-input"
                    value={searchTerm}
                    onChange={(e) => { setSearchTerm(e.target.value); setTablePage(1); }}
                    style={{ maxWidth: 220, padding: "6px 12px", fontSize: 12 }}
                  />
                </div>

                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Target Timestamp</th>
                        <th>Step</th>
                        <th>Predicted Demand</th>
                        <th>Unit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedPoints.map((pt, idx) => (
                        <tr key={pt.timestamp}>
                          <td style={{ color: "var(--color-text-muted)" }}>
                            {(tablePage - 1) * pageSize + idx + 1}
                          </td>
                          <td className="font-mono">
                            {formatTimestamp(pt.timestamp)}
                          </td>
                          <td>
                            <span className="badge badge-info">
                              +{(tablePage - 1) * pageSize + idx + 1}h
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, color: "var(--color-primary)" }}>
                            {pt.predicted_energy_kwh.toFixed(3)}
                          </td>
                          <td style={{ color: "var(--color-text-muted)" }}>kWh</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Table Pagination */}
                {totalTablePages > 1 && (
                  <div className="pagination">
                    <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
                      Page {tablePage} of {totalTablePages}
                    </span>
                    <div style={{ display: "flex", gap: 6 }}>
                      <button
                        onClick={() => setTablePage((p) => Math.max(1, p - 1))}
                        disabled={tablePage === 1}
                        className="btn btn-secondary btn-sm"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setTablePage((p) => Math.min(totalTablePages, p + 1))}
                        disabled={tablePage === totalTablePages}
                        className="btn btn-secondary btn-sm"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="card" style={{ minHeight: 400, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <EmptyState
                icon="🔮"
                title="No Forecast Generated Yet"
                description="Select your forecast origin timestamp and horizon on the left, then click 'Generate Multi-Step Forecast'."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
