// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FingerprintResponse, OptimizeResponse } from "../src/types/scene";

const health = vi.fn();
const fingerprint = vi.fn();
const optimize = vi.fn();

vi.mock("../src/api/solverClient", () => ({
  SolverClient: vi.fn(() => ({ health, fingerprint, optimize }))
}));

// Imported after the mock so App picks up the mocked client.
const { default: App } = await import("../src/ui/App");

const fingerprintResponse: FingerprintResponse = {
  schemaVersion: "1.0.0",
  approximation: true,
  scores: {
    visualMass: 0.5,
    hierarchy: 0.5,
    readingPath: 0.5,
    alignment: 0.5,
    negativeSpace: 0.5,
    grouping: 0.5
  },
  notes: []
};

const optimizeResponse: OptimizeResponse = {
  schemaVersion: "1.0.0",
  solverKind: "deterministic-reflow",
  target: { width: 1200, height: 628 },
  boxes: [],
  geneDrift: {
    visualMass: 0.11,
    hierarchy: 0.11,
    readingPath: 0.11,
    alignment: 0.11,
    negativeSpace: 0.11,
    grouping: 0.11
  },
  explanation: [{ code: "reflow", message: "Reflowed the design into the target.", metrics: {} }]
};

beforeEach(() => {
  health.mockReset();
  fingerprint.mockReset();
  optimize.mockReset();
});

describe("App", () => {
  it("runs the engine and shows the explanation when the solver is online", async () => {
    health.mockResolvedValue(true);
    fingerprint.mockResolvedValue(fingerprintResponse);
    optimize.mockResolvedValue(optimizeResponse);

    render(<App />);

    await waitFor(() => expect(screen.getByText("Engine online")).toBeInTheDocument());
    expect(screen.getByText("Reflowed the design into the target.")).toBeInTheDocument();
    expect(optimize).toHaveBeenCalled();
  });

  it("reports an offline engine and does not call optimize", async () => {
    health.mockResolvedValue(false);

    render(<App />);

    await waitFor(() => expect(screen.getByText("Engine offline")).toBeInTheDocument());
    expect(optimize).not.toHaveBeenCalled();
  });

  it("surfaces a solver error as an alert", async () => {
    health.mockResolvedValue(true);
    fingerprint.mockResolvedValue(fingerprintResponse);
    optimize.mockRejectedValue(new Error("Solver request failed (500)"));

    render(<App />);

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("Solver request failed (500)");
  });
});
