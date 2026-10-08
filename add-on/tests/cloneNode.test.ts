import { describe, expect, it, vi } from "vitest";

import { cloneNode } from "../src/documentSandbox/cloneNode";
import type { CloneSourceNode, PlacedNode } from "../src/documentSandbox/cloneNode";
import type { Color } from "../src/types/scene";

/** Fake created nodes that also record how they were made, for assertions. */
interface FakeTextNode extends PlacedNode {
  kind: "text";
  content: string;
}
interface FakeShapeNode extends PlacedNode {
  kind: "rectangle" | "ellipse" | "path";
  pathData?: string;
}
interface FakeFill {
  kind: "colorFill";
  color: Color;
}
interface FakeGroupNode extends PlacedNode {
  kind: "group";
  childNodes: PlacedNode[];
  children: { append(node: PlacedNode): void };
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
  const factories = {
    createText: vi.fn((textContent: string): FakeTextNode => ({
      kind: "text",
      content: textContent
    })),
    createRectangle: vi.fn((): FakeShapeNode => ({ kind: "rectangle" })),
    createEllipse: vi.fn((): FakeShapeNode => ({ kind: "ellipse" })),
    createPath: vi.fn((path: string): FakeShapeNode => ({ kind: "path", pathData: path })),
    createGroup: vi.fn((): FakeGroupNode => {
      const childNodes: PlacedNode[] = [];
      return {
        kind: "group",
        childNodes,
        children: {
          append: (node: PlacedNode) => {
            childNodes.push(node);
          }
        }
      };
    }),
    makeColorFill: vi.fn((color: Color): FakeFill => ({ kind: "colorFill", color }))
  };
  return { factories, targetArtboard, appended };
}

describe("cloneNode", () => {
  it("reconstructs a text source as an appended text node with identity copied", () => {
    const { factories, targetArtboard, appended } = makeHarness();
    const source: CloneSourceNode = {
      id: "headline",
      type: "Text",
      translation: { x: 12, y: 34 },
      rotation: 5,
      opacity: 0.8,
      fullContent: { text: "A city in motion" }
    };

    const clone = cloneNode(source, factories, targetArtboard) as FakeTextNode | null;

    expect(factories.createText).toHaveBeenCalledWith("A city in motion");
    expect(clone).not.toBeNull();
    expect(clone).toMatchObject({
      kind: "text",
      content: "A city in motion",
      translation: { x: 12, y: 34 },
      rotation: 5,
      opacity: 0.8
    });
    expect(targetArtboard.children.append).toHaveBeenCalledTimes(1);
    expect(appended).toEqual([clone]);

    // cloneNode does identity only; final geometry is applyLayout's job.
    expect(clone?.width).toBeUndefined();
    expect(clone?.height).toBeUndefined();
  });

  it("falls back to allTextContent when fullContent.text is absent", () => {
    const { factories, targetArtboard } = makeHarness();
    const source: CloneSourceNode = { id: "sub", type: "text", allTextContent: "Subhead" };

    cloneNode(source, factories, targetArtboard);

    expect(factories.createText).toHaveBeenCalledWith("Subhead");
  });

  it("reconstructs a rectangle source via createRectangle with identity and fill copied", () => {
    const { factories, targetArtboard, appended } = makeHarness();
    const red: Color = { r: 0.9, g: 0.1, b: 0.1, a: 1 };
    const source: CloneSourceNode = {
      id: "panel",
      type: "Rectangle",
      translation: { x: 4, y: 8 },
      rotation: 0,
      opacity: 0.5,
      fill: { color: red }
    };

    const clone = cloneNode(source, factories, targetArtboard) as FakeShapeNode | null;

    expect(factories.createRectangle).toHaveBeenCalledTimes(1);
    expect(factories.createEllipse).not.toHaveBeenCalled();
    expect(clone).toMatchObject({
      kind: "rectangle",
      translation: { x: 4, y: 8 },
      opacity: 0.5,
      fill: { kind: "colorFill", color: red }
    });
    expect(factories.makeColorFill).toHaveBeenCalledWith(red);
    expect(appended).toEqual([clone]);
    // Geometry still deferred to applyLayout.
    expect(clone?.width).toBeUndefined();
    expect(clone?.height).toBeUndefined();
  });

  it("reconstructs an ellipse source via createEllipse", () => {
    const { factories, targetArtboard, appended } = makeHarness();
    const source: CloneSourceNode = { id: "dot", type: "Ellipse", opacity: 1 };

    const clone = cloneNode(source, factories, targetArtboard) as FakeShapeNode | null;

    expect(factories.createEllipse).toHaveBeenCalledTimes(1);
    expect(clone?.kind).toBe("ellipse");
    expect(appended).toEqual([clone]);
  });

  it("leaves the default fill when the source has no readable fill color", () => {
    const { factories, targetArtboard } = makeHarness();
    const source: CloneSourceNode = { id: "plain", type: "Rectangle", opacity: 1 };

    const clone = cloneNode(source, factories, targetArtboard);

    expect(factories.makeColorFill).not.toHaveBeenCalled();
    expect(clone?.fill).toBeUndefined();
  });

  it("recreates a path only when a path string is present, else returns null", () => {
    const withPath = makeHarness();
    const pathSource: CloneSourceNode = { id: "swoosh", type: "Path", path: "M0 0 L10 10 Z" };
    const pathClone = cloneNode(pathSource, withPath.factories, withPath.targetArtboard);
    expect(withPath.factories.createPath).toHaveBeenCalledWith("M0 0 L10 10 Z");
    expect(pathClone).not.toBeNull();

    const noPath = makeHarness();
    const emptySource: CloneSourceNode = { id: "swoosh", type: "Path" };
    const nullClone = cloneNode(emptySource, noPath.factories, noPath.targetArtboard);
    expect(noPath.factories.createPath).not.toHaveBeenCalled();
    expect(nullClone).toBeNull();
    expect(noPath.appended).toEqual([]);
  });

  it("returns null and appends nothing for image sources (pixels cannot be recreated from bounds)", () => {
    for (const type of ["Image", "MediaContainer"]) {
      const { factories, targetArtboard, appended } = makeHarness();
      const clone = cloneNode({ id: "x", type }, factories, targetArtboard);
      expect(clone).toBeNull();
      expect(factories.createText).not.toHaveBeenCalled();
      expect(factories.createRectangle).not.toHaveBeenCalled();
      expect(factories.createGroup).not.toHaveBeenCalled();
      expect(targetArtboard.children.append).not.toHaveBeenCalled();
      expect(appended).toEqual([]);
    }
  });

  it("reconstructs a group: created + appended once, supported children into the group, unsupported skipped", () => {
    const { factories, targetArtboard, appended } = makeHarness();
    const source: CloneSourceNode = {
      id: "story",
      type: "Group",
      translation: { x: 1, y: 2 },
      opacity: 0.9,
      children: [
        { id: "t", type: "Text", fullContent: { text: "Hi" } },
        { id: "r", type: "Rectangle" },
        { id: "img", type: "Image" } // unsupported -> skipped
      ]
    };

    const group = cloneNode(source, factories, targetArtboard) as FakeGroupNode | null;

    expect(factories.createGroup).toHaveBeenCalledTimes(1);
    expect(group).toMatchObject({ kind: "group", translation: { x: 1, y: 2 }, opacity: 0.9 });

    // The group (only) is appended to the artboard; children go INTO the group.
    expect(appended).toEqual([group]);
    expect(group?.childNodes.map((node) => (node as FakeTextNode | FakeShapeNode).kind)).toEqual([
      "text",
      "rectangle"
    ]);
    expect(factories.createText).toHaveBeenCalledWith("Hi");
    expect(factories.createRectangle).toHaveBeenCalledTimes(1);
  });

  it("reconstructs an empty group: created + appended with no children", () => {
    const { factories, targetArtboard, appended } = makeHarness();
    const group = cloneNode(
      { id: "empty", type: "Group" },
      factories,
      targetArtboard
    ) as FakeGroupNode | null;

    expect(factories.createGroup).toHaveBeenCalledTimes(1);
    expect(appended).toEqual([group]);
    expect(group?.childNodes).toEqual([]);
  });
});
