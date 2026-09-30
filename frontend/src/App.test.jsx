import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "./App.jsx";
import { NAV_ITEMS } from "./layouts/MainLayout.jsx";

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App routing", () => {
  it("shows all navigation links", () => {
    renderAt("/");
    const nav = screen.getByRole("navigation", { name: /main navigation/i });
    for (const item of NAV_ITEMS) {
      expect(nav).toHaveTextContent(item.label);
    }
  });

  it.each([
    ["/", "Dashboard"],
    ["/forecast", "Forecast"],
    ["/history", "History"],
    ["/model", "Model"],
    ["/about", "About"],
  ])("renders %s page", (path, heading) => {
    renderAt(path);
    expect(screen.getByRole("heading", { level: 2, name: heading })).toBeInTheDocument();
  });

  it("falls back to the dashboard for unknown routes", () => {
    renderAt("/does-not-exist");
    expect(screen.getByRole("heading", { level: 2, name: "Dashboard" })).toBeInTheDocument();
  });
});
