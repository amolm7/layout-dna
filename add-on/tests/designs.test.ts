import { describe, expect, it } from "vitest";

import { DESIGNS, findDesign } from "../src/ui/designs";

describe("design gallery", () => {
  it("exposes at least three curated designs", () => {
    expect(DESIGNS.length).toBeGreaterThanOrEqual(3);
  });

  it("gives every design a stable id, name, and well-formed scene", () => {
    const ids = new Set<string>();
    for (const design of DESIGNS) {
      expect(design.id).toBeTruthy();
      expect(design.name).toBeTruthy();
      expect(ids.has(design.id)).toBe(false);
      ids.add(design.id);

      expect(design.scene.schemaVersion).toBe("1.0.0");
      expect(design.scene.canvas.width).toBeGreaterThan(0);
      expect(design.scene.canvas.height).toBeGreaterThan(0);
      expect(design.scene.elements.length).toBeGreaterThan(0);
    }
  });

  it("resolves a design by id and falls back to the first entry", () => {
    expect(findDesign("retail-promo").id).toBe("retail-promo");
    expect(findDesign("does-not-exist").id).toBe(DESIGNS[0]!.id);
  });
});
