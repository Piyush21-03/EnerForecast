import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { Alert, Button, DataTable, Pagination, StatCard } from "./index.js";

describe("Button", () => {
  it("calls onClick and defaults to type=button", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    const btn = screen.getByRole("button", { name: "Go" });
    expect(btn).toHaveAttribute("type", "button");
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled while loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
  });
});

describe("StatCard", () => {
  it("shows an em dash when there is no value, and the unit", () => {
    render(<StatCard label="Peak" unit="kWh" value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("kWh")).toBeInTheDocument();
  });

  it("shows the value when provided", () => {
    render(<StatCard label="Peak" unit="kWh" value="4.25" />);
    expect(screen.getByText("4.25")).toBeInTheDocument();
  });
});

describe("Alert", () => {
  it("uses role=alert for errors", () => {
    render(<Alert variant="error" title="Oops">Something failed</Alert>);
    expect(screen.getByRole("alert")).toHaveTextContent("Something failed");
  });
});

describe("DataTable", () => {
  const columns = [
    { key: "name", header: "Name", sortable: true },
    { key: "value", header: "Value", align: "right" },
  ];

  it("renders rows and custom cell renderers", () => {
    const cols = [{ key: "value", header: "Value", render: (r) => `${r.value} kWh` }];
    render(<DataTable columns={cols} rows={[{ id: 1, value: 2 }]} />);
    expect(screen.getByText("2 kWh")).toBeInTheDocument();
  });

  it("shows the empty message and loading state", () => {
    const { rerender } = render(<DataTable columns={columns} rows={[]} emptyMessage="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    rerender(<DataTable columns={columns} rows={[]} loading />);
    expect(screen.getByRole("status", { name: "Loading table" })).toBeInTheDocument();
  });

  it("reports sort clicks and exposes aria-sort", () => {
    const onSort = vi.fn();
    render(<DataTable columns={columns} rows={[]} sortKey="name" sortDirection="desc" onSort={onSort} />);
    expect(screen.getByRole("columnheader", { name: /Name/ })).toHaveAttribute("aria-sort", "descending");
    fireEvent.click(screen.getByRole("button", { name: /Name/ }));
    expect(onSort).toHaveBeenCalledWith("name");
  });
});

describe("Pagination", () => {
  it("disables Previous on the first page and Next on the last", () => {
    const { rerender } = render(<Pagination page={1} pageSize={10} total={25} onPageChange={() => {}} />);
    expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    rerender(<Pagination page={3} pageSize={10} total={25} onPageChange={() => {}} />);
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("requests the neighbouring page", () => {
    const onPageChange = vi.fn();
    render(<Pagination page={2} pageSize={10} total={25} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(onPageChange).toHaveBeenNthCalledWith(1, 3);
    expect(onPageChange).toHaveBeenNthCalledWith(2, 1);
  });

  it("handles zero results", () => {
    render(<Pagination page={1} pageSize={10} total={0} onPageChange={() => {}} />);
    expect(screen.getByText(/Page 1 of 1/)).toBeInTheDocument();
  });
});
