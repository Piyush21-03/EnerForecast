import { NavLink, Outlet } from "react-router-dom";

import { cn } from "../utils/cn.js";

export const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/forecast", label: "Forecast" },
  { to: "/history", label: "History" },
  { to: "/model", label: "Model" },
  { to: "/about", label: "About" },
];

const linkClass = ({ isActive }) =>
  cn(
    "whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors",
    isActive ? "bg-emerald-50 text-emerald-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  );

export default function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <h1 className="flex items-center gap-2 text-lg font-bold text-slate-900">
            <svg className="h-6 w-6 text-emerald-600" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" />
            </svg>
            Energy Consumption Forecasting
          </h1>
          <nav aria-label="Main navigation" className="-mx-1 flex gap-1 overflow-x-auto px-1">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Energy values in kWh · Model trained offline in Google Colab; this app serves inference only
      </footer>
    </div>
  );
}
