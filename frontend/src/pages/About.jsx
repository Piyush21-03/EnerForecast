import { Accordion } from "../components/Accordion";

export default function About() {
  const techStack = [
    { icon: "⚡", name: "FastAPI", desc: "High-performance asynchronous Python API framework with auto OpenAPI documentation" },
    { icon: "🤖", name: "LightGBM", desc: "Microsoft's high-speed gradient boosted decision trees optimized for time series regression" },
    { icon: "🗄️", name: "PostgreSQL", desc: "Production relational database storing historical loads, forecast records, and telemetry" },
    { icon: "⚛️", name: "React 18 + Vite", desc: "Ultra-fast modern SPA frontend with rich glassmorphism UI and dynamic telemetry" },
    { icon: "📊", name: "Recharts", desc: "Composable SVG charting library providing interactive load trajectories and crosshairs" },
    { icon: "🐍", name: "SQLAlchemy & Alembic", desc: "Enterprise database ORM layer with declarative models and migration capabilities" },
  ];

  const accordionItems = [
    {
      title: "🔮 How Recursive Multi-Step Forecasting Operates",
      content: (
        <div>
          <p style={{ marginBottom: 10 }}>
            Forecasting energy demand over an extended horizon (e.g., 24 hours to 7 days) requires recursive prediction:
          </p>
          <ol style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6 }}>
            <li>At step <em>t + 1</em>, features (such as <code>lag_1</code>, <code>rolling_mean_24</code>) are computed solely from historical observations up to time <em>t</em>.</li>
            <li>The LightGBM model predicts the energy demand at <em>t + 1</em>.</li>
            <li>This prediction is appended to the working historical buffer, allowing subsequent steps (<em>t + 2</em>, <em>t + 3</em>, ...) to derive their required lags dynamically from earlier predictions.</li>
            <li>Actual future readings are <strong>never</strong> accessed, guaranteeing complete isolation from lookahead leakage.</li>
          </ol>
        </div>
      ),
    },
    {
      title: "📐 Feature Engineering Design (24 Columns)",
      content: (
        <div>
          <p style={{ marginBottom: 8 }}>
            The pipeline transforms the univariate hourly energy time series into 24 specialized features:
          </p>
          <ul style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6 }}>
            <li><strong>Autoregressive Lags</strong>: <code>lag_1</code>, <code>lag_2</code>, <code>lag_3</code> (short-term persistence), <code>lag_24</code>, <code>lag_48</code> (daily diurnal cycle), <code>lag_168</code> (weekly periodicity).</li>
            <li><strong>Rolling Aggregations</strong>: Rolling means and sample standard deviations over <code>3h</code>, <code>6h</code>, <code>24h</code>, and <code>168h</code> windows computed on the shifted series.</li>
            <li><strong>Calendar Components</strong>: Hour of day (0-23), day of month (1-31), day of week (0-6), month (1-12), ISO week of year, and weekend binary flag.</li>
            <li><strong>Cyclical Trigonometric Projections</strong>: Sine and cosine transforms of the hour (period 24) and day of the week (period 7) to preserve circular continuity across midnight and week boundaries.</li>
          </ul>
        </div>
      ),
    },
    {
      title: "📡 REST API Architecture & Endpoints",
      content: (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ background: "var(--color-surface-elevated)", padding: 10, borderRadius: 8 }}>
            <span className="badge badge-success font-mono">POST /predict</span>
            <div style={{ fontSize: 12, marginTop: 4, color: "var(--color-text-secondary)" }}>
              Accepts <code>timestamp</code> (forecast origin) and <code>horizon</code> (1-168h). Returns sequential predictions and persists to DB.
            </div>
          </div>
          <div style={{ background: "var(--color-surface-elevated)", padding: 10, borderRadius: 8 }}>
            <span className="badge badge-success font-mono">POST /batch-predict</span>
            <div style={{ fontSize: 12, marginTop: 4, color: "var(--color-text-secondary)" }}>
              Processes multiple independent forecast requests in a single transaction.
            </div>
          </div>
          <div style={{ background: "var(--color-surface-elevated)", padding: 10, borderRadius: 8 }}>
            <span className="badge badge-info font-mono">GET /energy/latest & /energy/history</span>
            <div style={{ fontSize: 12, marginTop: 4, color: "var(--color-text-secondary)" }}>
              Provides historical observations with optional hourly or daily aggregation.
            </div>
          </div>
          <div style={{ background: "var(--color-surface-elevated)", padding: 10, borderRadius: 8 }}>
            <span className="badge badge-info font-mono">GET /health</span>
            <div style={{ fontSize: 12, marginTop: 4, color: "var(--color-text-secondary)" }}>
              Reports deep readiness: model loaded in memory, history data loaded, and PostgreSQL connection state.
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title" style={{ fontSize: 26 }}>System Architecture & Engineering</h1>
        <p className="page-subtitle" style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>
          Overview of the machine learning pipeline, inference design, and technology stack
        </p>
      </div>

      {/* Technology Stack Grid */}
      <div className="card mb-4" style={{ marginBottom: 28 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Technology Ecosystem</h3>
            <p className="card-subtitle">End-to-end full-stack machine learning production architecture</p>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {techStack.map((tech) => (
            <div
              key={tech.name}
              style={{
                background: "var(--color-surface-elevated)",
                border: "1px solid var(--color-border)",
                borderRadius: 14,
                padding: "16px 18px",
                display: "flex",
                gap: 14,
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  fontSize: 24,
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: "var(--color-surface)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  border: "1px solid var(--color-border)",
                }}
              >
                {tech.icon}
              </div>
              <div>
                <h4 style={{ fontSize: 14.5, fontWeight: 700, marginBottom: 4 }}>{tech.name}</h4>
                <p style={{ fontSize: 12.5, color: "var(--color-text-muted)", lineHeight: 1.5, margin: 0 }}>
                  {tech.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Accordion Guide */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Engineering Deep Dive & Methodology</h3>
            <p className="card-subtitle">Frequently consulted topics regarding inference and data safety</p>
          </div>
        </div>

        <Accordion items={accordionItems} />
      </div>
    </div>
  );
}
