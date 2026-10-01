import { cn } from "../utils/cn.js";
import Spinner from "./Spinner.jsx";

const ALIGN = { left: "text-left", right: "text-right", center: "text-center" };

/**
 * columns: [{ key, header, align?, sortable?, render?(row) }]
 * Sorting is controlled by the parent via sortKey / sortDirection ("asc" | "desc") / onSort(key).
 */
export default function DataTable({
  columns,
  rows,
  rowKey = "id",
  loading = false,
  emptyMessage = "No data to display.",
  sortKey,
  sortDirection,
  onSort,
}) {
  const ariaSort = (col) => {
    if (!col.sortable) return undefined;
    if (col.key !== sortKey) return "none";
    return sortDirection === "asc" ? "ascending" : "descending";
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                aria-sort={ariaSort(col)}
                className={cn("px-4 py-3 font-semibold text-slate-600", ALIGN[col.align || "left"])}
              >
                {col.sortable ? (
                  <button type="button" onClick={() => onSort?.(col.key)} className="inline-flex items-center gap-1 hover:text-slate-900">
                    {col.header}
                    <span aria-hidden="true">{col.key === sortKey ? (sortDirection === "asc" ? "▲" : "▼") : ""}</span>
                  </button>
                ) : (
                  col.header
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-10 text-center">
                <Spinner label="Loading table" />
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-10 text-center text-slate-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row[rowKey]} className="hover:bg-slate-50">
                {columns.map((col) => (
                  <td key={col.key} className={cn("px-4 py-3 text-slate-700", ALIGN[col.align || "left"])}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
