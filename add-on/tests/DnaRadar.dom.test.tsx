// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FingerprintResponse } from "../src/types/scene";
import { DnaRadar } from "../src/ui/DnaRadar";

const fingerprint: FingerprintResponse = {
  schemaVersion: "1.0.0",
  approximation: true,
  scores: {
    visualMass: 0.9,
    hierarchy: 0.8,
    readingPath: 0.7,
    alignment: 0.6,
    negativeSpace: 0.5,
    grouping: 0.4
  },
  notes: []
};

describe("DnaRadar", () => {
  it("renders each gene score as a rounded percentage", () => {
    render(<DnaRadar fingerprint={fingerprint} />);
    expect(screen.getByText("Measured proxy")).toBeInTheDocument();
    // visualMass 0.9 -> 90, grouping 0.4 -> 40
    expect(screen.getByText("90")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
  });

  it("labels itself as a preview with placeholder values when no fingerprint is given", () => {
    render(<DnaRadar fingerprint={null} />);
    expect(screen.getByText("Preview")).toBeInTheDocument();
    // Every gene falls back to 0.58 -> 58 when unmeasured.
    expect(screen.getAllByText("58")).toHaveLength(6);
  });

  it("exposes the radar as an accessible image", () => {
    render(<DnaRadar fingerprint={fingerprint} />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("fingerprint");
  });
});
