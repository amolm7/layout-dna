import { describe, expect, it, vi } from "vitest";

import type { CloneSourceNode, PlacedNode } from "../src/documentSandbox/cloneNode";
import {
  buildNodeFactories,
  makeCloneInto,
  resolveTargetArtboard
} from "../src/documentSandbox/cloningAdapter";
import type { Color } from "../src/types/scene";

function makeFakeEditor() {
  return {
    createText: vi.fn((textContent: string) => ({ id: "text", textContent })),
    createRectangle: vi.fn(() => ({ id: "rect" })),
    createEllipse: vi.fn(() => ({ id: "ellipse" })),
    createPath: vi.fn((path: string) => ({ id: `path-${path}` })),
    createGroup: vi.fn(() => ({ id: "group", children: { append: vi.fn() } })),
    makeColorFill: vi.fn((color: Color) => ({ kind: "colorFill", color }))
  };
}

function makeTargetPageWithArtboard() {
  const appended: PlacedNode[] = [];
  const artboard = {
    children: {
      append: vi.fn((node: PlacedNode) => {
        appended.push(node);
      })
    }
  };
  return { targetPage: { artboards: { first: artboard } }, artboard, appended };
}

describe("cloningAdapter", () => {
  it("buildNodeFactories wires every factory through to the editor", () => {
    const editor = makeFakeEditor();
    const factories = buildNodeFactories(editor);
    const red: Color = { r: 1, g: 0, b: 0, a: 1 };

    factories.createText("hi");
    factories.createRectangle();
    factories.createEllipse();
    factories.createPath("M0 0");
    factories.createGroup();
    factories.makeColorFill(red);

    expect(editor.createText).toHaveBeenCalledWith("hi");
    expect(editor.createRectangle).toHaveBeenCalledTimes(1);
    expect(editor.createEllipse).toHaveBeenCalledTimes(1);
    expect(editor.createPath).toHaveBeenCalledWith("M0 0");
    expect(editor.createGroup).toHaveBeenCalledTimes(1);
    expect(editor.makeColorFill).toHaveBeenCalledWith(red);
  });

  it("resolveTargetArtboard returns the first artboard, or null when absent", () => {
    const { targetPage, artboard } = makeTargetPageWithArtboard();
    expect(resolveTargetArtboard(targetPage)).toBe(artboard);

    expect(resolveTargetArtboard({})).toBeNull();
    expect(resolveTargetArtboard({ artboards: {} })).toBeNull();
  });

  it("makeCloneInto delegates to cloneNode: a text source is appended to the target artboard", () => {
    const editor = makeFakeEditor();
    const { targetPage, appended } = makeTargetPageWithArtboard();
    const cloneInto = makeCloneInto(editor, targetPage);
    const source: CloneSourceNode = {
      id: "headline",
      type: "Text",
      fullContent: { text: "Hello" }
    };

    const clone = cloneInto(source);

    expect(editor.createText).toHaveBeenCalledWith("Hello");
    expect(clone).not.toBeNull();
    expect(appended).toEqual([clone]);
  });

  it("makeCloneInto returns null for every source when the target page has no artboard", () => {
    const editor = makeFakeEditor();
    const cloneInto = makeCloneInto(editor, { artboards: {} });
    const source: CloneSourceNode = {
      id: "headline",
      type: "Text",
      fullContent: { text: "Hello" }
    };

    expect(cloneInto(source)).toBeNull();
    expect(editor.createText).not.toHaveBeenCalled();
  });
});
