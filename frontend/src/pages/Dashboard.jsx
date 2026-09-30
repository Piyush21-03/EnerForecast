import { Card, ChartPlaceholder, PageHeader, StatCard } from "../components";

const STATS = [
  { label: "Latest Energy", unit: "kWh" },
  { label: "24-Hour Forecast (total)", unit: "kWh" },
  { label: "Peak Forecast", unit: "kWh" },
  { label: "Average Forecast", unit: "kWh" },
  { label: "Minimum Forecast", unit: "kWh" },
  { label: "Model MAE", unit: "kWh" },
  { label: "Model RMSE", unit: "kWh" },
];

const CHARTS = [
  "Historical Energy Consumption",
  "24-Hour Forecast",
  "Actual vs Predicted",
  "Daily Consumption",
  "Weekly Consumption",
];

export default function Dashboard() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Household energy_kwh (hourly) — latest values, forecast summary and model accuracy. All energy values are in kWh."
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((s) => (
          <StatCard key={s.label} label={s.label} unit={s.unit} value={null} hint="Loaded from the API in Phase 11" />
        ))}
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {CHARTS.map((title) => (
          <Card key={title} title={title} subtitle="kWh">
            <ChartPlaceholder label={title} />
          </Card>
        ))}
      </div>
    </div>
  );
}
