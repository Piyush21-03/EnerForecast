import { useLocation, useNavigate } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";

const pageTitles = {
  "/": "Dashboard",
  "/forecast": "Forecast",
  "/history": "History",
  "/model": "Model Telemetry",
  "/about": "Architecture & Specs",
};

export default function HeaderBar({ health, onOpenQuickPredict, onToggleMobileNav }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const currentTitle = pageTitles[location.pathname] || "Dashboard";
  const statusCls = health?.status === "ok" ? "ok" : health?.status === "error" ? "error" : "degraded";

  return (
    <header className="top-header">
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <button
          onClick={onToggleMobileNav}
          className="btn btn-ghost btn-sm btn-icon"
          style={{ display: "none" }}
          id="mobile-nav-toggle"
          aria-label="Toggle navigation menu"
        >
          ☰
        </button>

        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <span>EnergyFC</span>
          <span>/</span>
          <span className="current">{currentTitle}</span>
        </nav>
      </div>

      <div className="header-actions">
        {/* API Status Badge */}
        <div
          className="badge"
          style={{
            background: "var(--color-surface-elevated)",
            border: "1px solid var(--color-border)",
            padding: "5px 12px",
            fontSize: 12,
            gap: 8,
          }}
        >
          <span className={`status-dot ${statusCls}`} />
          <span style={{ color: "var(--color-text-secondary)" }}>API:</span>
          <strong style={{ textTransform: "capitalize" }}>{health?.status || "Connecting..."}</strong>
        </div>

        {/* Quick Forecast Launch Button */}
        <button
          onClick={onOpenQuickPredict}
          className="btn btn-primary btn-sm"
          style={{ gap: 6 }}
        >
          <span>🌤️</span>
          <span>Quick Forecast</span>
        </button>

        {/* Theme Switcher Button */}
        <button
          onClick={toggleTheme}
          className="btn btn-secondary btn-icon btn-sm"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>

        {/* User Profile / Logout */}
        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: 10, paddingLeft: 12, borderLeft: "1px solid var(--color-border)" }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "var(--color-surface-hover)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 16,
              }}
            >
              {user.avatar || "👤"}
            </div>
            <div style={{ display: "flex", flexDirection: "column", marginRight: 8 }} className="hide-on-mobile">
              <span style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.2 }}>{user.name}</span>
              <span style={{ fontSize: 11, color: "var(--color-text-muted)", lineHeight: 1.2 }}>{user.role}</span>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="btn btn-ghost btn-sm"
              style={{ padding: "6px 10px", color: "var(--color-danger)" }}
              title="Sign Out"
            >
              Log Out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
