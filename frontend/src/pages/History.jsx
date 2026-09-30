import { Card, DataTable, PageHeader } from "../components";

const COLUMNS = [
  { key: "prediction_timestamp", header: "Timestamp", sortable: true },
  { key: "predicted_energy_kwh", header: "Predicted Energy (kWh)", align: "right", sortable: true },
  { key: "model_version", header: "Model Version" },
  { key: "horizon", header: "Horizon (h)", sortable: true },
  { key: "created_at", header: "Created", sortable: true },
];

export default function History() {
  return (
    <div>
      <PageHeader title="History" description="Forecasts previously generated and stored in the database." />
      <Card>
        <DataTable columns={COLUMNS} rows={[]} emptyMessage="No stored forecasts to show yet." />
      </Card>
    </div>
  );
}
