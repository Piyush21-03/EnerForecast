import { useEffect, useState, useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { Link } from "react-router-dom";
import { getEnergyHistory, getHealth, getLatestEnergy, getModelInfo } from "../services/api";
import { SkeletonCard, SkeletonChart } from "../components/Skeleton";
import { useToast } from "../context/ToastContext";

function fmtDate(ts) {
  return new Date(ts).toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const val = Number(payload[0].value);
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
        {new Date(label).toLocaleString("en-IN", {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span style={{ fontSize: 18, fontWeight: 800, color: "var(--color-primary)" }}>
          {val.toFixed(3)}
        </span>
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>kWh</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [latest, setLatest] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState(60);
  const [showOnboarding, setShowOnboarding] = useState(() => {
    try {
      return localStorage?.getItem("energyfc_onboarding_dismissed") !== "true";
    } catch {
      return false;
    }
  });
  const { toast } = useToast();

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      getHealth(),
      getLatestEnergy(),
      getEnergyHistory("daily", timeframe),
      getModelInfo(),
    ]).then(([h, l, c, m]) => {
      if (h.status === "fulfilled") setHealth(h.value);
      if (l.status === "fulfilled") setLatest(l.value);
      if (c.status === "fulfilled") setHistoryData(c.value.points || []);
      if (m.status === "fulfilled") setModelInfo(m.value);
      setLoading(false);
    });
  }, [timeframe]);

  const dismissOnboarding = () => {
    setShowOnboarding(false);
    localStorage.setItem("energyfc_onboarding_dismissed", "true");
  };

  const chartPoints = useMemo(() => {
    return historyData.map((d) => ({
      timestamp: d.timestamp,
      energy_kwh: Number(Number(d.energy_kwh).toFixed(3)),
    }));
  }, [historyData]);

  const avgKwh = useMemo(() => {
    if (!chartPoints.length) return 0;
    const sum = chartPoints.reduce((acc, p) => acc + p.energy_kwh, 0);
    return sum / chartPoints.length;
  }, [chartPoints]);

  const peakKwh = useMemo(() => {
    if (!chartPoints.length) return 0;
    return Math.max(...chartPoints.map((p) => p.energy_kwh));
  }, [chartPoints]);

  const downloadHistoryCsv = () => {
    if (!chartPoints.length) return;
    const headers = "timestamp,energy_kwh\n";
    const rows = chartPoints.map((p) => `${p.timestamp},${p.energy_kwh}`).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `energy_history_${timeframe}d.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${chartPoints.length} history records as CSV!`);
  };

  return (
    <div className="fade-in">
      {/* Onboarding Banner */}
      {showOnboarding && (
        <div className="onboarding-banner">
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span style={{ fontSize: 28 }}>🌿</span>
            <div>
              <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 2 }}>
                Welcome to EnergyFC Studio
              </h4>
              <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: 0 }}>
                High-precision multi-step energy load forecasting with LightGBM. Generate instant forecasts or explore telemetry.
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Link to="/forecast" className="btn btn-primary btn-sm">
              Try a Forecast →
            </Link>
            <button
              onClick={dismissOnboarding}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: 16, padding: "4px 8px" }}
              aria-label="Dismiss banner"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Page Title & Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title" style={{ fontSize: 26 }}>Operational Dashboard</h1>
          <p className="page-subtitle" style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>
            Telemetry, historical baseline consumption, and model inference state
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={downloadHistoryCsv} className="btn btn-secondary btn-sm" disabled={!chartPoints.length}>
            <span>📥 Export CSV</span>
          </button>
          <Link to="/forecast" className="btn btn-primary btn-sm">
            <span>🌤️ New Forecast</span>
          </Link>
        </div>
      </div>

      {/* Stat KPI Cards */}
      <div className="stat-grid">
        {loading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            {/* Latest Reading */}
            <div className="stat-card card-lift">
              <div className="stat-top">
                <div className="stat-icon-wrap" style={{ color: "var(--color-primary)" }}>☀️</div>
                <span className="stat-trend up">
                  <span>●</span> Live
                </span>
              </div>
              <div className="stat-label">Latest Meter Reading</div>
              <div className="stat-value accent">
                {latest ? Number(latest.energy_kwh).toFixed(3) : "—"}
                <span style={{ fontSize: 14, fontWeight: 500, marginLeft: 4, color: "var(--color-text-muted)" }}>kWh</span>
              </div>
              <div className="stat-unit">
                {latest ? new Date(latest.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"} (Observed)
              </div>
            </div>

            {/* Timeframe Average */}
            <div className="stat-card card-lift">
              <div className="stat-top">
                <div className="stat-icon-wrap" style={{ color: "var(--color-accent)" }}>📈</div>
                <span className="stat-trend neutral">
                  <span>Avg</span>
                </span>
              </div>
              <div className="stat-label">{timeframe}-Day Average</div>
              <div className="stat-value">
                {avgKwh ? avgKwh.toFixed(3) : "—"}
                <span style={{ fontSize: 14, fontWeight: 500, marginLeft: 4, color: "var(--color-text-muted)" }}>kWh</span>
              </div>
              <div className="stat-unit">Peak: {peakKwh.toFixed(2)} kWh</div>
            </div>

            {/* Model Architecture */}
            <div className="stat-card card-lift">
              <div className="stat-top">
                <div className="stat-icon-wrap" style={{ color: "var(--color-success)" }}>🌱</div>
                <span className="badge badge-success">
                  {modelInfo?.model_version ? `v${modelInfo.model_version}` : "Active"}
                </span>
              </div>
              <div className="stat-label">Model Pipeline</div>
              <div className="stat-value" style={{ fontSize: 22, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                LightGBM
              </div>
              <div className="stat-unit">{modelInfo?.feature_count || 24} dynamic lag features</div>
            </div>

            {/* Database & System */}
            <div className="stat-card card-lift">
              <div className="stat-top">
                <div className="stat-icon-wrap" style={{ color: "var(--color-info)" }}>🏺</div>
                <span className={`badge ${health?.database_ok ? "badge-success" : "badge-warning"}`}>
                  {health?.database_ok ? "Synced" : "Offline"}
                </span>
              </div>
              <div className="stat-label">PostgreSQL Database</div>
              <div className="stat-value" style={{ fontSize: 22 }}>
                {health?.database_ok ? "Healthy" : "Degraded"}
              </div>
              <div className="stat-unit">{chartPoints.length} hourly/daily records loaded</div>
            </div>
          </>
        )}
      </div>

      {/* Main Historical Chart Card */}
      <div className="card card-lift mb-4" style={{ marginBottom: 24 }}>
        <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
          <div>
            <h3 className="card-title">Historical Consumption Trajectory</h3>
            <p className="card-subtitle">Aggregated energy demand series used as lookback context for inference</p>
          </div>

          {/* Timeframe Segmented Control */}
          <div className="tabs-nav">
            {[7, 30, 60, 90].map((days) => (
              <button
                key={days}
                className={`tab-btn ${timeframe === days ? "active" : ""}`}
                onClick={() => setTimeframe(days)}
              >
                {days}D
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <SkeletonChart />
        ) : (
          <div style={{ height: 340, width: "100%" }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartPoints} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="energyFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.6} />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={fmtDate}
                  stroke="var(--color-text-muted)"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  stroke="var(--color-text-muted)"
                  fontSize={11}
                  tickLine={false}
                  unit=" kWh"
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine
                  y={avgKwh}
                  stroke="var(--color-accent)"
                  strokeDasharray="4 4"
                  label={{
                    value: `Avg: ${avgKwh.toFixed(2)}`,
                    fill: "var(--color-text-secondary)",
                    fontSize: 11,
                    position: "insideTopRight",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="energy_kwh"
                  stroke="var(--color-primary)"
                  strokeWidth={2.5}
                  fill="url(#energyFill)"
                  activeDot={{ r: 6, fill: "var(--color-primary)", stroke: "var(--color-surface)", strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Quick Action & Info Strip */}
      <div className="grid-3">
        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>🔮</div>
          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Generate Forecasts</h4>
          <p style={{ fontSize: 12.5, color: "var(--color-text-muted)", marginBottom: 14 }}>
            Predict recursive hourly load from 1 to 168 hours ahead with continuous feature updates.
          </p>
          <Link to="/forecast" className="btn btn-secondary btn-sm" style={{ width: "100%" }}>
            Go to Forecasting →
          </Link>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>📋</div>
          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Audit History</h4>
          <p style={{ fontSize: 12.5, color: "var(--color-text-muted)", marginBottom: 14 }}>
            Review past forecast runs, latency metrics, and database execution records.
          </p>
          <Link to="/history" className="btn btn-secondary btn-sm" style={{ width: "100%" }}>
            Browse Logs →
          </Link>
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>🤖</div>
          <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>Model Telemetry</h4>
          <p style={{ fontSize: 12.5, color: "var(--color-text-muted)", marginBottom: 14 }}>
            Examine feature importance, cross-validation metrics, and training hyperparameters.
          </p>
          <Link to="/model" className="btn btn-secondary btn-sm" style={{ width: "100%" }}>
            Inspect Architecture →
          </Link>
        </div>
      </div>
    </div>
  );
}
