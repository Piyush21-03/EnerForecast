import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import App from "../App";
import { ThemeProvider } from "../context/ThemeContext";
import { ToastProvider } from "../context/ToastContext";

describe("App", () => {
  it("renders without crashing and displays header and nav", () => {
    render(
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    );
    expect(screen.getAllByText(/EnergyFC/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /forecast/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /history/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /model/i }).length).toBeGreaterThanOrEqual(1);
  });
});
