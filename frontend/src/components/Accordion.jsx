import { useState } from "react";

export function Accordion({ items }) {
  const [openIndex, setOpenIndex] = useState(0);

  const toggle = (idx) => {
    setOpenIndex((prev) => (prev === idx ? null : idx));
  };

  return (
    <div className="accordion">
      {items.map((item, idx) => {
        const isOpen = openIndex === idx;
        return (
          <div key={idx} className="accordion-item">
            <div className="accordion-header" onClick={() => toggle(idx)}>
              <span>{item.title}</span>
              <span
                style={{
                  transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.2s ease",
                  fontSize: 12,
                  color: "var(--color-text-muted)",
                }}
              >
                ▼
              </span>
            </div>
            {isOpen && <div className="accordion-body">{item.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
