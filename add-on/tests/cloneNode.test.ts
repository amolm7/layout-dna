import { describe, expect, it, vi } from "vitest";

import { cloneNode } from "../src/documentSandbox/cloneNode";
import type { CloneSourceNode, PlacedNode } from "../src/documentSandbox/cloneNode";

/** A fake created text node that also records the content it was seeded with. */
interface FakeTextNode extends PlacedNode {
  kind: "text";
  content: string;
}

function makeHarness() {
  const appended: PlacedNode[] = [];
  const targetArtboard = {
    children: {
      append: vi.fn((node: PlacedNode) => {
        appended.push(node);
      })
    }
  };
  const createText = vi.fn((textContent: string): FakeTextNode => ({
    kind: "text",
    content: textContent
  }));
  const factories = { createText };
  return { factories, targetArtboard, appended, createText };
}

describe("cloneNode", () => {
  it("reconstructs a text source as an appended text node with identity copied", () => {
    const { factories, targetArtboard, appended, createText } = makeHarness();
    const source: CloneSourceNode = {
      id: "headline",
      type: "Text",
      translation: { x: 12, y: 34 },
      rotation: 5,
      opacity: 0.8,
      fullContent: { text: "A city in motion" }
    };

    const clone = cloneNode(source, factories, targetArtboard) as FakeTextNode | null;

    expect(createText).toHaveBeenCalledWith("A city in motion");
    expect(clone).not.toBeNull();
    expect(clone).toMatchObject({
      kind: "text",
      content: "A city in motion",
      translation: { x: 12, y: 34 },
      rotation: 5,
      opacity: 0.8
    });

    // Appended exactly once, and the appended node is the one returned.
    expect(targetArtboard.children.append).toHaveBeenCalledTimes(1);
    expect(appended).toEqual([clone]);

    // cloneNode does identity only; final geometry is applyLayout's job.
    expect(clone?.width).toBeUndefined();
    expect(clone?.height).toBeUndefined();
  });

  it("falls back to allTextContent when fullContent.text is absent", () => {
    const { factories, targetArtboard, createText } = makeHarness();
    const source: CloneSourceNode = { id: "sub", type: "text", allTextContent: "Subhead" };

    cloneNode(source, factories, targetArtboard);

    expect(createText).toHaveBeenCalledWith("Subhead");
  });

  it("returns null and appends nothing for a non-text source (type not yet supported)", () => {
    const { factories, targetArtboard, appended, createText } = makeHarness();
    const source: CloneSourceNode = { id: "logo", type: "rectangle", opacity: 1 };

    const clone = cloneNode(source, factories, targetArtboard);

    expect(clone).toBeNull();
    expect(createText).not.toHaveBeenCalled();
    expect(targetArtboard.children.append).not.toHaveBeenCalled();
    expect(appended).toEqual([]);
  });
});
