import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useTheme } from "../context/ThemeContext";

export default function Login() {
  const [email, setEmail] = useState("piyush@energyfc.ai");
  const [password, setPassword] = useState("demo12345");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [mode, setMode] = useState("signin"); // 'signin' | 'signup'
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const { toast } = useToast();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSignIn = (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.warning("Please enter your email and password.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      login(email, password);
      toast.success(`Welcome back, ${email.split("@")[0]}! Entering Studio…`);
      setLoading(false);
      navigate("/");
    }, 600);
  };

  const handleDemoAccess = () => {
    setLoading(true);
    setTimeout(() => {
      login("demo.analyst@energyfc.ai", "demo");
      toast.success("Logged in with Demo Analyst access! Welcome!");
      setLoading(false);
      navigate("/");
    }, 400);
  };

  return (
    <div className="login-page-wrap">
      {/* Ambient Floating Blurred Orbs */}
      <div className="floating-orb orb-1" />
      <div className="floating-orb orb-2" />
      <div className="floating-orb orb-3" />

      {/* Floating Telemetry Badges (Desktop) */}
      <div className="floating-badge badge-top-left">
        <div style={{ fontSize: 24 }}>☀️</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--color-text)" }}>
            Live Demand: 2.028 kWh
          </div>
          <div style={{ fontSize: 11, color: "var(--color-success)", fontWeight: 600 }}>
            ● Normal Diurnal Cycle
          </div>
        </div>
      </div>

      <div className="floating-badge badge-top-right">
        <div style={{ fontSize: 24 }}>🌱</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--color-text)" }}>
            LightGBM GBDT
          </div>
          <div style={{ fontSize: 11, color: "var(--color-primary)", fontWeight: 600 }}>
            R² Score: 0.8360 (High Accuracy)
          </div>
        </div>
      </div>

      <div className="floating-badge badge-bottom-left">
        <div style={{ fontSize: 24 }}>🌤️</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--color-text)" }}>
            Recursive 168h Horizon
          </div>
          <div style={{ fontSize: 11, color: "var(--color-text-muted)" }}>
            Zero Lookahead Data Leakage
          </div>
        </div>
      </div>

      <div className="floating-badge badge-bottom-right">
        <div style={{ fontSize: 24 }}>🏺</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--color-text)" }}>
            PostgreSQL Cluster
          </div>
          <div style={{ fontSize: 11, color: "var(--color-info)", fontWeight: 600 }}>
            8,760 Hourly Observations Synced
          </div>
        </div>
      </div>

      {/* Top Floating Controls */}
      <div
        style={{
          position: "absolute",
          top: 24,
          right: 28,
          zIndex: 20,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <button
          onClick={toggleTheme}
          className="btn btn-secondary btn-icon btn-sm"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>

      {/* Main Glassmorphism Landing & Auth Card */}
      <div className="login-container">
        {/* Left Hero Pane */}
        <div className="login-hero">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
              <div className="sidebar-logo-icon" style={{ width: 48, height: 48, fontSize: 24 }}>
                🌿
              </div>
              <div className="sidebar-logo-text" style={{ fontSize: 22 }}>
                EnergyFC
                <span style={{ fontSize: 11 }}>Predictive Intelligence</span>
              </div>
            </div>

            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 14px",
                borderRadius: 20,
                background: "var(--color-surface-elevated)",
                border: "1px solid var(--color-border)",
                fontSize: 12,
                fontWeight: 600,
                color: "var(--color-primary)",
                marginBottom: 20,
              }}
            >
              <span>●</span> Machine Learning Production Studio
            </div>

            <h1
              style={{
                fontSize: 32,
                fontWeight: 800,
                lineHeight: 1.2,
                letterSpacing: "-0.03em",
                marginBottom: 16,
              }}
            >
              Predict Electric Load with{" "}
              <span
                style={{
                  background: "var(--color-primary-gradient)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Microsecond Precision
              </span>
            </h1>

            <p style={{ fontSize: 14.5, color: "var(--color-text-secondary)", lineHeight: 1.6, marginBottom: 28 }}>
              Automated multi-step recursive forecasting with continuous lag synthesis, cyclical trigonometric encoding, and real-time telemetry analytics.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {[
                "24 Dynamic Lag & Rolling Window Features",
                "Recursive Autoregressive Horizon (1 to 168 Hours)",
                "Full PostgreSQL Audit Logging & Latency Tracking",
                "Enterprise FastAPI Serving & Interactive Studio",
              ].map((feat) => (
                <div key={feat} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13.5 }}>
                  <span
                    style={{
                      width: 22,
                      height: 22,
                      borderRadius: "50%",
                      background: "var(--color-success-bg)",
                      color: "var(--color-success)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    ✓
                  </span>
                  <span style={{ color: "var(--color-text)" }}>{feat}</span>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              padding: "16px 20px",
              borderRadius: 16,
              background: "var(--color-surface-elevated)",
              border: "1px solid var(--color-border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginTop: 32,
            }}
          >
            <div>
              <div style={{ fontSize: 11, textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                Active Production Estimator
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, marginTop: 2 }}>
                LightGBM Regressor v1.0.0
              </div>
            </div>
            <span className="badge badge-success">Active</span>
          </div>
        </div>

        {/* Right Form Pane */}
        <div className="login-form-pane">
          <div style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 6 }}>
              {mode === "signin" ? "Sign In to Studio" : "Create Studio Account"}
            </h2>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
              {mode === "signin"
                ? "Enter your credentials to access energy forecasts and telemetry."
                : "Register a new operator profile for model experimentation."}
            </p>
          </div>

          {/* Mode Tabs */}
          <div className="tabs-nav" style={{ width: "100%", marginBottom: 24 }}>
            <button
              type="button"
              className={`tab-btn ${mode === "signin" ? "active" : ""}`}
              onClick={() => setMode("signin")}
              style={{ flex: 1, textAlign: "center", padding: "8px 0" }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`tab-btn ${mode === "signup" ? "active" : ""}`}
              onClick={() => setMode("signup")}
              style={{ flex: 1, textAlign: "center", padding: "8px 0" }}
            >
              Register
            </button>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSignIn} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">
                <span>Email Address</span>
              </label>
              <div style={{ position: "relative" }}>
                <span
                  style={{
                    position: "absolute",
                    left: 14,
                    top: "50%",
                    transform: "translateY(-50%)",
                    fontSize: 16,
                    color: "var(--color-text-muted)",
                    pointerEvents: "none",
                  }}
                >
                  ✉️
                </span>
                <input
                  id="login-email"
                  type="email"
                  placeholder="analyst@energyfc.ai"
                  className="form-input"
                  style={{ paddingLeft: 42 }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="login-password">
                <span>Password</span>
                {mode === "signin" && (
                  <button
                    type="button"
                    onClick={() => toast.info("Use demo credentials or click 1-Click Demo Access below.")}
                    style={{
                      background: "transparent",
                      color: "var(--color-primary)",
                      fontSize: 11,
                      cursor: "pointer",
                      border: "none",
                      padding: 0,
                    }}
                  >
                    Forgot password?
                  </button>
                )}
              </label>
              <div style={{ position: "relative" }}>
                <span
                  style={{
                    position: "absolute",
                    left: 14,
                    top: "50%",
                    transform: "translateY(-50%)",
                    fontSize: 16,
                    color: "var(--color-text-muted)",
                    pointerEvents: "none",
                  }}
                >
                  🔒
                </span>
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="form-input"
                  style={{ paddingLeft: 42, paddingRight: 42 }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontSize: 14,
                    padding: 4,
                  }}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 13 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  style={{ accentColor: "var(--color-primary)" }}
                />
                <span style={{ color: "var(--color-text-secondary)" }}>Remember this workstation</span>
              </label>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
              style={{ width: "100%", padding: 13, gap: 10, marginTop: 4 }}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 18, height: 18, border: "2px solid #fff", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                  <span>Authenticating…</span>
                </>
              ) : (
                <>
                  <span>🌿</span>
                  <span>{mode === "signin" ? "Enter the Studio" : "Create Account"}</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Divider */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              margin: "24px 0 18px",
              color: "var(--color-text-muted)",
              fontSize: 11.5,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
            <span>OR INSTANT GUEST PASS</span>
            <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
          </div>

          {/* 1-Click Demo Login Button */}
          <button
            type="button"
            onClick={handleDemoAccess}
            className="btn btn-secondary btn-lg"
            disabled={loading}
            style={{ width: "100%", padding: 12, gap: 8 }}
          >
            <span>🌾</span>
            <span>1-Click Instant Demo Access</span>
          </button>
        </div>
      </div>
    </div>
  );
}
