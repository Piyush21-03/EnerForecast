/** Stand-in shown until real charts are added in Phase 12. */
export default function ChartPlaceholder({ label = "Chart", height = "h-64" }) {
  return (
    <div
      className={`flex ${height} items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-400`}
    >
      {label} — available after API integration
    </div>
  );
}
