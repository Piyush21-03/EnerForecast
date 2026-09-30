import { Button, Card, ChartPlaceholder, DataTable, PageHeader } from "../components";

const COLUMNS = [
  { key: "timestamp", header: "Timestamp" },
  { key: "predicted_energy_kwh", header: "Predicted Energy", align: "right" },
  { key: "unit", header: "Unit" },
];

export default function Forecast() {
  return (
    <div>
      <PageHeader title="Forecast" description="Generate an hourly energy_kwh forecast from the latest available observation." />
      <div className="space-y-6">
        <Card title="Forecast settings">
          <fieldset className="flex flex-wrap items-center gap-6">
            <legend className="sr-only">Forecast horizon</legend>
            {[24, 168].map((h) => (
              <label key={h} className="flex items-center gap-2 text-sm text-slate-700">
                <input type="radio" name="horizon" value={h} defaultChecked={h === 24} disabled />
                {h} hours
              </label>
            ))}
            <Button disabled>Generate Forecast</Button>
          </fieldset>
          <p className="mt-3 text-xs text-slate-400">Enabled once the page is connected to the API (Phase 13).</p>
        </Card>
        <Card title="Forecast chart" subtitle="kWh">
          <ChartPlaceholder label="Forecast chart" />
        </Card>
        <Card title="Forecast table">
          <DataTable columns={COLUMNS} rows={[]} emptyMessage="Generate a forecast to see hourly predictions." />
        </Card>
      </div>
    </div>
  );
}
