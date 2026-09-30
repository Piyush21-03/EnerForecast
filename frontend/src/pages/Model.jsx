import { Card, ChartPlaceholder, PageHeader, StatCard } from "../components";

const FACTS = [
  ["Dataset", "UCI Individual Household Electric Power Consumption"],
  ["Target", "energy_kwh"],
  ["Frequency", "Hourly"],
  ["Default forecast horizon", "24 hours"],
];

const METRICS = ["MAE", "RMSE", "sMAPE", "R²"];

export default function Model() {
  return (
    <div>
      <PageHeader
        title="Model"
        description="The selected model is chosen based on the project's validation results; no universal ranking of algorithms is implied."
      />
      <div className="space-y-6">
        <Card title="Model details">
          <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">Model</dt>
              <dd className="font-medium text-slate-900">—</dd>
            </div>
            {FACTS.map(([term, value]) => (
              <div key={term}>
                <dt className="text-slate-500">{term}</dt>
                <dd className="font-medium text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {METRICS.map((m) => (
            <StatCard key={m} label={m} value={null} hint="From the exported metrics.json (Phase 11)" />
          ))}
        </div>
        <Card title="Feature importance">
          <ChartPlaceholder label="Feature importance" />
        </Card>
      </div>
    </div>
  );
}
