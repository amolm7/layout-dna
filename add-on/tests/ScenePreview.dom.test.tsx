// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { SceneElement } from "../src/types/scene";
import type { PlacedElement } from "../src/ui/scenePlacement";
import { ScenePreview } from "../src/ui/ScenePreview";

function element(
  overrides: Partial<SceneElement> & Pick<SceneElement, "id" | "semanticRole">
): SceneElement {
  return {
    type: "shape",
    parentId: null,
    x: 0,
    y: 0,
    width: 0.1,
    height: 0.1,
    rotation: 0,
    zIndex: 0,
    visible: true,
    optional: false,
    visual: { opacity: 1, luminance: 0.5, colorCoverage: 1 },
    constraints: {},
    readingOrder: null,
    groupAffinities: [],
    ...overrides
  };
}

function placed(el: SceneElement): PlacedElement {
  return { element: el, x: el.x, y: el.y, width: el.width, height: el.height };
}

describe("ScenePreview", () => {
  it("renders text content for text roles", () => {
    const headline = element({
      id: "h",
      semanticRole: "headline",
      type: "text",
      text: { content: "A city in motion", fontSize: 80, fontWeight: 700 }
    });
    render(<ScenePreview canvas={{ width: 1000, height: 1000 }} placed={[placed(headline)]} />);
    expect(screen.getByText("A city in motion")).toBeInTheDocument();
  });

  it("derives the accessible label and caption from the badge", () => {
    render(<ScenePreview canvas={{ width: 1200, height: 628 }} placed={[]} badge="1200 x 628" />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("1200 x 628 layout preview");
    expect(screen.getByText("1200 x 628").tagName.toLowerCase()).toBe("figcaption");
  });

  it("falls back to a generic label without a badge", () => {
    render(<ScenePreview canvas={{ width: 100, height: 100 }} placed={[]} />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("Layout preview");
  });
});
