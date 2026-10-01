export default function EmptyState({ icon = "📊", title = "No data found", description = "Try adjusting your filters or generating a new forecast.", action }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 20,
          background: "var(--color-surface-elevated)",
          border: "1px solid var(--color-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 30,
          marginBottom: 16,
          boxShadow: "var(--shadow-sm)",
        }}
      >
        {icon}
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>{title}</h3>
      <p style={{ fontSize: 13, color: "var(--color-text-muted)", maxWidth: 360, marginBottom: action ? 18 : 0 }}>
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
