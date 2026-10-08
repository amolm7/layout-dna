import { describe, expect, it } from "vitest";

import { applyLayout } from "../src/documentSandbox/applyLayout";
import type { ElementBox } from "../src/types/scene";

interface FakeNode {
  id: string;
  width: number;
  height: number;
  translation: { x: number; y: number };
  rotation: number;
}

function sourceNode(id: string): FakeNode {
  return { id, width: 100, height: 50, translation: { x: 10, y: 20 }, rotation: 0 };
}

/**
 * Fake Document Sandbox editor with a populated SOURCE page and an empty TARGET page. `cloneInto`
 * stands in for the real adapter: it reconstructs a fresh node on the target (never handing back
 * the source object) and appends it, so we can assert the source is left untouched. Ids listed in
 * `unclonable` model nodes the real adapter cannot reproduce — `cloneInto` returns null for them.
 */
function makeEditor(unclonable: Set<string> = new Set()) {
  const sourceDescendants = [sourceNode("hero"), sourceNode("headline")];
  const targetChildren: FakeNode[] = [];
  const targetPage = { id: "target-1", children: targetChildren };

  const editor = {
    sourcePage: { artboards: { first: { allDescendants: sourceDescendants } } },
    targetPage,
    cloneInto(node: FakeNode): FakeNode | null {
      if (unclonable.has(node.id)) {
        return null;
      }
      const clone: FakeNode = {
        id: node.id,
        width: node.width,
        height: node.height,
        translation: { x: node.translation.x, y: node.translation.y },
        rotation: node.rotation
      };
      targetChildren.push(clone);
      return clone;
    }
  };

  return { editor, sourceDescendants, targetChildren };
}

function box(id: string, x: number, y: number, width: number, height: number): ElementBox {
  return { id, x, y, width, height, rotation: 0 };
}

describe("applyLayout", () => {
  it("clones source nodes onto the target page and applies the solved geometry to the clones", () => {
    const { editor, targetChildren } = makeEditor();
    const boxes = [box("hero", 0.1, 0.2, 0.5, 0.25), box("headline", 0.05, 0.6, 0.4, 0.1)];

    const result = applyLayout(editor as never, boxes, 800, 1000);

    expect(result.applied).toEqual(["hero", "headline"]);
    expect(result.missing).toEqual([]);

    // Both clones landed on the previously empty target page.
    expect(targetChildren.map((node) => node.id)).toEqual(["hero", "headline"]);

    const heroClone = targetChildren.find((node) => node.id === "hero");
    expect(heroClone).toMatchObject({
      width: 0.5 * 800,
      height: 0.25 * 1000,
      translation: { x: 0.1 * 800, y: 0.2 * 1000 },
      rotation: 0
    });
  });

  it("leaves the source page untouched (original width/height/translation/rotation)", () => {
    const { editor, sourceDescendants } = makeEditor();
    const boxes = [box("hero", 0.1, 0.2, 0.5, 0.25), box("headline", 0.05, 0.6, 0.4, 0.1)];

    applyLayout(editor as never, boxes, 800, 1000);

    for (const node of sourceDescendants) {
      expect(node).toMatchObject({
        width: 100,
        height: 50,
        translation: { x: 10, y: 20 },
        rotation: 0
      });
    }
  });

  it("reports ids in missing[] only when they cannot be found or cloned", () => {
    const { editor, targetChildren, sourceDescendants } = makeEditor(new Set(["headline"]));
    const boxes = [
      box("hero", 0.1, 0.2, 0.5, 0.25), // present + clonable -> applied
      box("headline", 0.05, 0.6, 0.4, 0.1), // present but cloneInto returns null -> missing
      box("ghost", 0, 0, 0.1, 0.1) // no matching source node -> missing
    ];

    const result = applyLayout(editor as never, boxes, 800, 1000);

    expect(result.applied).toEqual(["hero"]);
    expect(result.missing).toEqual(["headline", "ghost"]);

    // Only the clonable node was placed; source remains intact.
    expect(targetChildren.map((node) => node.id)).toEqual(["hero"]);
    for (const node of sourceDescendants) {
      expect(node).toMatchObject({ width: 100, height: 50, translation: { x: 10, y: 20 } });
    }
  });
});
