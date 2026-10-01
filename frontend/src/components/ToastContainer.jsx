import { useToast } from "../context/ToastContext";

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  if (!toasts || toasts.length === 0) return null;

  const icons = {
    success: "✓",
    error: "✕",
    warning: "⚠️",
    info: "ℹ️",
  };

  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span style={{ fontSize: 16 }}>{icons[t.type]}</span>
          <div style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{t.message}</div>
          <button
            onClick={() => removeToast(t.id)}
            style={{
              background: "transparent",
              color: "var(--color-text-muted)",
              fontSize: 14,
              padding: 4,
            }}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
