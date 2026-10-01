import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, Navigate } from "react-router-dom";
import { getHealth } from "../services/api";
import HeaderBar from "../components/HeaderBar";
import QuickPredictModal from "../components/QuickPredictModal";
import ToastContainer from "../components/ToastContainer";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/",         icon: "🏡", label: "Dashboard",   badge: "Live" },
  { to: "/forecast", icon: "🌤️", label: "Forecast",    badge: "AI" },
  { to: "/history",  icon: "🗂️", label: "History",     badge: null },
  { to: "/model",    icon: "🌱", label: "Model Info",  badge: "v1.0" },
  { to: "/about",    icon: "🏛️",  label: "Architecture",badge: null },
];

export default function MainLayout() {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [quickPredictOpen, setQuickPredictOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const location = useLocation();

  // Close mobile drawer when location changes
  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "degraded", model_loaded: false }));
  }, []);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const statusCls = health?.status === "ok" ? "ok" : health?.status === "error" ? "error" : "degraded";

  return (
    <div className="app-shell">
      {/* Mobile Backdrop */}
      {mobileNavOpen && (
        <div className="sidebar-backdrop" onClick={() => setMobileNavOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${mobileNavOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🌿</div>
          <div className="sidebar-logo-text">
            EnergyFC
            <span>Forecasting Studio</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-label">Core Platform</div>
          {navItems.map(({ to, icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <span className="nav-icon">{icon}</span>
              <span style={{ flex: 1 }}>{label}</span>
              {badge && (
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: 6,
                    background: "var(--color-surface-hover)",
                    color: "var(--color-primary)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  {badge}
                </span>
              )}
            </NavLink>
          ))}

          <div style={{ margin: "20px 0 10px", height: 1, background: "var(--color-border-subtle)" }} />
          <div className="sidebar-label">System Health</div>

          <div
            className="card"
            style={{
              padding: 14,
              borderRadius: 14,
              margin: "6px 4px 16px",
              background: "var(--color-surface-elevated)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontWeight: 600 }}>Inference Core</span>
              <span className={`status-dot ${statusCls}`} />
            </div>
            <div style={{ fontSize: 11.5, color: "var(--color-text-muted)", display: "flex", flexDirection: "column", gap: 3 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>LightGBM:</span>
                <span style={{ color: health?.model_loaded ? "var(--color-success)" : "var(--color-danger)", fontWeight: 600 }}>
                  {health?.model_loaded ? "Active" : "Offline"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>PostgreSQL:</span>
                <span style={{ color: health?.database_ok ? "var(--color-success)" : "var(--color-warning)", fontWeight: 600 }}>
                  {health?.database_ok ? "Connected" : "Offline"}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => setQuickPredictOpen(true)}
            className="btn btn-primary btn-sm"
            style={{ width: "calc(100% - 8px)", margin: "0 auto", padding: 10 }}
          >
            🌤️ New Forecast
          </button>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <HeaderBar
          health={health}
          onOpenQuickPredict={() => setQuickPredictOpen(true)}
          onToggleMobileNav={() => setMobileNavOpen((prev) => !prev)}
        />
        <div className="content-body">
          <Outlet />
        </div>
      </main>

      {/* Global Quick Predict Modal */}
      <QuickPredictModal
        isOpen={quickPredictOpen}
        onClose={() => setQuickPredictOpen(false)}
      />

      {/* Global Toast Notifications Stack */}
      <ToastContainer />
    </div>
  );
}
