import { useState, useEffect } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Modal from "./Modal";
import { getLatestEnergy, predict } from "../services/api";
import { useToast } from "../context/ToastContext";

export default function QuickPredictModal({ isOpen, onClose }) {
  const [timestamp, setTimestamp] = useState("");
  const [horizon, setHorizon] = useState(24);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen && !timestamp) {
      getLatestEnergy()
        .then((data) => {
          if (data?.timestamp) {
            const d = new Date(data.timestamp);
            const pad = (n) => String(n).padStart(2, "0");
            const formatted = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
            setTimestamp(formatted);
          }
        })
        .catch(() => {
          const now = new Date();
          now.setMinutes(0, 0, 0);
          const pad = (n) => String(n).padStart(2, "0");
          setTimestamp(`${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:00`);
        });
    }
  }, [isOpen, timestamp]);

  const handleRun = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await predict(timestamp, Number(horizon));
      setResult(data);
      toast.success(`Generated ${data.forecast.length}h energy forecast!`);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Failed to generate forecast";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const chartData = (result?.forecast || []).map((p) => ({
    time: new Date(p.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    kWh: Number(p.predicted_energy_kwh.toFixed(3)),
  }));

  const totalKwh = chartData.reduce((acc, c) => acc + c.kWh, 0);
  const peakKwh = chartData.length ? Math.max(...chartData.map((c) => c.kWh)) : 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="⚡ Quick Multi-Step Forecast">
      <form onSubmit={handleRun} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="form-group">
          <label className="form-label" htmlFor="quick-ts">
            <span>Forecast Origin (Timestamp)</span>
            <span style={{ fontSize: 11, color: "var(--color-primary)" }}>Hour-aligned</span>
          </label>
          <input
            id="quick-ts"
            type="datetime-local"
            className="form-input"
            value={timestamp}
            onChange={(e) => setTimestamp(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="quick-horizon">
            <span>Forecast Horizon: {horizon} Hours</span>
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
            {[6, 12, 24, 48, 72, 168].map((h) => (
              <button
                key={h}
                type="button"
                className={`preset-chip ${horizon === h ? "active" : ""}`}
                onClick={() => setHorizon(h)}
              >
                {h >= 24 ? `${h / 24}d` : `${h}h`}
              </button>
            ))}
          </div>
          <input
            id="quick-horizon"
            type="range"
            min={1}
            max={168}
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            style={{ width: "100%", accentColor: "var(--color-primary)" }}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", padding: 12 }}>
          {loading ? "Generating Forecast…" : "Run Forecast Model"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: 24, animation: "slideUp 0.3s ease" }}>
          <div className="divider" style={{ margin: "16px 0", height: 1, background: "var(--color-border)" }} />
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, fontSize: 13 }}>
            <div>
              <span className="text-muted">Total: </span>
              <strong>{totalKwh.toFixed(2)} kWh</strong>
            </div>
            <div>
              <span className="text-muted">Peak: </span>
              <strong className="text-accent">{peakKwh.toFixed(2)} kWh</strong>
            </div>
            <div>
              <span className="text-muted">Model: </span>
              <span>{result.model_version}</span>
            </div>
          </div>

          <div style={{ height: 180, width: "100%", background: "var(--color-surface-elevated)", borderRadius: 12, padding: 8 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="quickGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "var(--color-text-muted)" }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "var(--color-text-muted)" }} tickLine={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <div className="card" style={{ padding: "6px 10px", fontSize: 12 }}>
                        <div>{payload[0].payload.time}</div>
                        <strong className="text-accent">{payload[0].value} kWh</strong>
                      </div>
                    );
                  }}
                />
                <Area type="monotone" dataKey="kWh" stroke="var(--color-primary)" fill="url(#quickGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </Modal>
  );
}
