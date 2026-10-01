import { useState } from "react";

export function Tooltip({ text, children, position = "top" }) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      style={{ position: "relative", display: "inline-flex", alignItems: "center" }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          style={{
            position: "absolute",
            bottom: position === "top" ? "calc(100% + 8px)" : "auto",
            top: position === "bottom" ? "calc(100% + 8px)" : "auto",
            left: "50%",
            transform: "translateX(-50%)",
            background: "var(--color-surface-elevated)",
            color: "var(--color-text)",
            border: "1px solid var(--color-border)",
            borderRadius: 8,
            padding: "5px 10px",
            fontSize: 11.5,
            fontWeight: 500,
            whiteSpace: "nowrap",
            boxShadow: "var(--shadow-md)",
            zIndex: 100,
            pointerEvents: "none",
            animation: "fadeIn 0.15s ease",
          }}
        >
          {text}
        </div>
      )}
    </div>
  );
}
