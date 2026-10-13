import { describe, expect, it } from "vitest";

import type { ElementBox, Scene } from "../src/types/scene";
import {
  colorToCss,
  droppedElements,
  isDarkBackground,
  placeScene,
  placeTarget
} from "../src/ui/scenePlacement";

const scene: Scene = {
  schemaVersion: "1.0.0",
  canvas: { width: 1000, height: 1000 },
  elements: [
    {
      id: "top",
      type: "text",
      semanticRole: "headline",
      parentId: null,
      x: 0.1,
      y: 0.1,
      width: 0.5,
      height: 0.1,
      rotation: 0,
      zIndex: 2,
      visible: true,
      optional: false,
      visual: { opacity: 1, luminance: 0.1, colorCoverage: 0.5 },
      constraints: {},
      readingOrder: 0,
      groupAffinities: []
    },
    {
      id: "back",
      type: "shape",
      semanticRole: "background",
      parentId: null,
      x: 0,
      y: 0,
      width: 1,
      height: 1,
      rotation: 0,
      zIndex: 0,
      visible: true,
      optional: true,
      visual: { opacity: 1, luminance: 0.9, colorCoverage: 1 },
      constraints: {},
      readingOrder: null,
      groupAffinities: []
    },
    {
      id: "hidden",
      type: "shape",
      semanticRole: "decoration",
      parentId: null,
      x: 0,
      y: 0,
      width: 0.2,
      height: 0.2,
      rotation: 0,
      zIndex: 5,
      visible: false,
      optional: true,
      visual: { opacity: 1, luminance: 0.5, colorCoverage: 1 },
      constraints: {},
      readingOrder: null,
      groupAffinities: []
    }
  ]
};

describe("placeScene", () => {
  it("drops invisible elements and sorts by z-index", () => {
    const placed = placeScene(scene);
    expect(placed.map((p) => p.element.id)).toEqual(["back", "top"]);
  });
});

describe("placeTarget", () => {
  const boxes: ElementBox[] = [
    { id: "top", x: 0.04, y: 0.04, width: 0.92, height: 0.2, rotation: 0 }
  ];

  it("maps boxes back onto their source elements", () => {
    const placed = placeTarget(scene, boxes);
    expect(placed).toHaveLength(1);
    expect(placed[0]!.element.id).toBe("top");
    expect(placed[0]!.width).toBe(0.92);
  });

  it("reports elements the solver dropped", () => {
    expect(droppedElements(scene, boxes).map((e) => e.id)).toEqual(["back"]);
  });
});

describe("color helpers", () => {
  it("converts normalized colors to rgba", () => {
    expect(colorToCss({ r: 1, g: 0, b: 0, a: 1 }, "x")).toBe("rgba(255, 0, 0, 1)");
    expect(colorToCss(undefined, "fallback")).toBe("fallback");
  });

  it("detects dark backgrounds by luminance", () => {
    expect(isDarkBackground({ r: 0.08, g: 0.12, b: 0.18, a: 1 })).toBe(true);
    expect(isDarkBackground({ r: 0.96, g: 0.93, b: 0.86, a: 1 })).toBe(false);
  });
});
