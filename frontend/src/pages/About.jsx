import { Card, PageHeader } from "../components";

export default function About() {
  return (
    <div>
      <PageHeader title="About" description="How this application is put together." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Project">
          <p className="text-sm leading-6 text-slate-700">
            An end-to-end energy consumption forecasting system. Data analysis, cleaning, feature engineering and model
            training happen in Google Colab; the trained model is exported and served by a FastAPI backend that never
            retrains it. Forecasts are stored in PostgreSQL and shown in this React dashboard.
          </p>
        </Card>
        <Card title="Dataset">
          <p className="text-sm leading-6 text-slate-700">
            UCI Individual Household Electric Power Consumption, processed into a 1-minute CSV with the target{" "}
            <code className="rounded bg-slate-100 px-1">energy_kwh</code> and the columns Global_reactive_power, Voltage,
            Global_intensity and Sub_metering_1–3. Forecasts are hourly and reported in kWh.
          </p>
        </Card>
      </div>
    </div>
  );
}
