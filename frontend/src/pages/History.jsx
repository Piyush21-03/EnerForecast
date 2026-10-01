import { useEffect, useState, useMemo } from "react";
import { getForecastHistory } from "../services/api";
import Modal from "../components/Modal";
import EmptyState from "../components/EmptyState";
import { useToast } from "../context/ToastContext";

function fmtDate(ts) {
  if (!ts) return "—";
  return new Date(ts).toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const SORT_OPTIONS = [
  { value: "created_at",           label: "Created Date" },
  { value: "prediction_timestamp", label: "Target Prediction Time" },
  { value: "predicted_energy_kwh", label: "Energy (kWh)" },
  { value: "horizon",              label: "Forecast Horizon" },
];

export default function History() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState("created_at");
  const [order, setOrder] = useState("desc");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const { toast } = useToast();

  const loadData = () => {
    setLoading(true);
    const params = { page, page_size: pageSize, sort_by: sortBy, order };
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    getForecastHistory(params)
      .then(setData)
      .catch(() => {
        setData(null);
        toast.error("Could not load forecast history records.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, pageSize, sortBy, order]);

  const handleApplyFilter = (e) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const handleResetFilter = () => {
    setDateFrom("");
    setDateTo("");
    setSearchQuery("");
    setSortBy("created_at");
    setOrder("desc");
    setPage(1);
  };

  const records = useMemo(() => {
    if (!data?.items) return [];
    if (!searchQuery) return data.items;
    const q = searchQuery.toLowerCase();
    return data.items.filter(
      (r) =>
        (r.request_id && r.request_id.toLowerCase().includes(q)) ||
        (r.model_version && r.model_version.toLowerCase().includes(q))
    );
  }, [data, searchQuery]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  const exportHistoryCsv = () => {
    if (!records.length) return;
    const headers = "id,request_id,forecast_origin,target_timestamp,predicted_energy_kwh,horizon,model_version,created_at\n";
    const rows = records
      .map(
        (r) =>
          `${r.id},${r.request_id},${r.forecast_timestamp},${r.prediction_timestamp},${r.predicted_energy_kwh},${r.horizon},${r.model_version},${r.created_at}`
      )
      .join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `forecast_history_page_${page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported current view as CSV!");
  };

  return (
    <div className="fade-in">
      {/* Title & Actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title" style={{ fontSize: 26 }}>Prediction History</h1>
          <p className="page-subtitle" style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>
            Audit log of all saved forecast executions and database points
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={loadData} className="btn btn-secondary btn-sm">
            🔄 Refresh
          </button>
          <button onClick={exportHistoryCsv} className="btn btn-primary btn-sm" disabled={!records.length}>
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Filter Card */}
      <div className="card mb-4" style={{ marginBottom: 24 }}>
        <form onSubmit={handleApplyFilter}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14, alignItems: "end" }}>
            <div className="form-group">
              <label className="form-label">Search Request ID</label>
              <input
                type="text"
                placeholder="Filter by UUID / model..."
                className="form-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Sort Attribute</label>
              <select
                className="form-select"
                value={sortBy}
                onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Order</label>
              <select
                className="form-select"
                value={order}
                onChange={(e) => { setOrder(e.target.value); setPage(1); }}
              >
                <option value="desc">Newest First (Desc)</option>
                <option value="asc">Oldest First (Asc)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Date From</label>
              <input
                type="date"
                className="form-input"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Date To</label>
              <input
                type="date"
                className="form-input"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                Filter
              </button>
              <button type="button" onClick={handleResetFilter} className="btn btn-secondary">
                Reset
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Main Table Card */}
      <div className="card">
        <div className="card-header" style={{ flexWrap: "wrap", gap: 12 }}>
          <div>
            <h3 className="card-title">Stored Prediction Records</h3>
            <p className="card-subtitle">
              Total records: <strong>{data?.total || 0}</strong>
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>Rows per page:</span>
            <select
              className="form-select"
              style={{ width: 75, padding: "4px 8px", fontSize: 12 }}
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <span className="spinner" style={{ width: 24, height: 24, border: "2px solid var(--color-primary)", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
            <div style={{ marginTop: 12, color: "var(--color-text-muted)", fontSize: 13 }}>Loading database records…</div>
          </div>
        ) : records.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Record ID</th>
                    <th>Target Hour</th>
                    <th>Predicted (kWh)</th>
                    <th>Horizon</th>
                    <th>Model</th>
                    <th>Created At</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((row) => (
                    <tr key={row.id}>
                      <td className="font-mono" style={{ color: "var(--color-text-muted)", fontSize: 12 }}>
                        #{row.id}
                      </td>
                      <td className="font-mono">
                        {fmtDate(row.prediction_timestamp)}
                      </td>
                      <td style={{ fontWeight: 700, color: "var(--color-primary)" }}>
                        {Number(row.predicted_energy_kwh).toFixed(3)}
                      </td>
                      <td>
                        <span className="badge badge-info">
                          {row.horizon}h
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-success">
                          {row.model_version}
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                        {fmtDate(row.created_at)}
                      </td>
                      <td>
                        <button
                          onClick={() => setSelectedRecord(row)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: "4px 10px", fontSize: 11.5 }}
                        >
                          Inspect 🔍
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="pagination">
              <span style={{ fontSize: 12.5, color: "var(--color-text-muted)" }}>
                Showing {(page - 1) * pageSize + 1} – {Math.min(page * pageSize, data?.total || 0)} of {data?.total || 0}
              </span>

              <div style={{ display: "flex", gap: 6 }}>
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="btn btn-secondary btn-sm"
                >
                  « First
                </button>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn btn-secondary btn-sm"
                >
                  ‹ Prev
                </button>
                <span
                  style={{
                    padding: "4px 12px",
                    display: "flex",
                    alignItems: "center",
                    fontSize: 12,
                    fontWeight: 600,
                    background: "var(--color-surface-elevated)",
                    borderRadius: 8,
                    border: "1px solid var(--color-border)",
                  }}
                >
                  Page {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn btn-secondary btn-sm"
                >
                  Next ›
                </button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page === totalPages}
                  className="btn btn-secondary btn-sm"
                >
                  Last »
                </button>
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            icon="📋"
            title="No Prediction Records Found"
            description="No forecasts match the active filters. Run a new forecast to populate the history table."
          />
        )}
      </div>

      {/* Record Inspection Modal */}
      {selectedRecord && (
        <Modal
          isOpen={Boolean(selectedRecord)}
          onClose={() => setSelectedRecord(null)}
          title={`🔍 Forecast Record #${selectedRecord.id}`}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 13 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div className="card" style={{ padding: 14 }}>
                <div className="stat-label">Predicted Load</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: "var(--color-primary)", marginTop: 4 }}>
                  {Number(selectedRecord.predicted_energy_kwh).toFixed(3)}
                  <span style={{ fontSize: 13, color: "var(--color-text-muted)", marginLeft: 4 }}>kWh</span>
                </div>
              </div>

              <div className="card" style={{ padding: 14 }}>
                <div className="stat-label">Horizon</div>
                <div style={{ fontSize: 24, fontWeight: 800, marginTop: 4 }}>
                  {selectedRecord.horizon}
                  <span style={{ fontSize: 13, color: "var(--color-text-muted)", marginLeft: 4 }}>Hours</span>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8, background: "var(--color-surface-elevated)", padding: 14, borderRadius: 12 }}>
              <div className="flex justify-between">
                <span className="text-muted">Target Prediction Time:</span>
                <strong>{fmtDate(selectedRecord.prediction_timestamp)}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Forecast Origin Timestamp:</span>
                <strong>{fmtDate(selectedRecord.forecast_timestamp)}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Model Version:</span>
                <span className="badge badge-success">{selectedRecord.model_version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Recorded In DB:</span>
                <span>{fmtDate(selectedRecord.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Request ID:</span>
                <span className="font-mono text-muted" style={{ fontSize: 11 }}>{selectedRecord.request_id}</span>
              </div>
            </div>

            <button
              onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(selectedRecord, null, 2));
                toast.success("Record details copied to clipboard!");
              }}
              className="btn btn-secondary btn-sm"
              style={{ width: "100%", padding: 10 }}
            >
              📋 Copy JSON Object
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
