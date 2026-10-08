import type { Color } from "../types/scene";
import { cloneNode } from "./cloneNode";
import type {
  CloneSourceNode,
  NodeFactories,
  PlacedGroupNode,
  PlacedNode,
  TargetArtboard
} from "./cloneNode";

/**
 * Wires the pure `cloneNode` reconstruction to the live Adobe Express editor.
 *
 * This activates the real reconstruct-via-factories path (there is no node clone API). The factory
 * names mapped here are confirmed against Adobe's Editor reference (createText/createRectangle/
 * createEllipse/createPath/createGroup/makeColorFill), but the end-to-end path is
 * IMPLEMENTED-BUT-UNVERIFIED against live Adobe Express — the tests exercise it with fakes only.
 * Property writability on live nodes (rotation is read-only; per-type geometry) and source fill-color
 * readability remain unverified; applyLayout already degrades a throwing geometry write to missing[].
 */

/** The subset of the Adobe editor the adapter calls; names/signatures mirror the Editor reference. */
export interface AdapterEditorLike {
  createText(textContent: string): PlacedNode;
  createRectangle(): PlacedNode;
  createEllipse(): PlacedNode;
  createPath(path: string): PlacedNode;
  createGroup(): PlacedGroupNode;
  makeColorFill(color: Color): unknown;
}

/** A target page as exposed by the sandbox; its first artboard is where clones are appended. */
export interface TargetPageLike {
  artboards?: { first?: TargetArtboard };
}

/** Map the live editor's factories onto the NodeFactories interface cloneNode consumes. */
export function buildNodeFactories(editor: AdapterEditorLike): NodeFactories {
  // Calls go through `editor` to preserve its `this` binding.
  return {
    createText: (textContent) => editor.createText(textContent),
    createRectangle: () => editor.createRectangle(),
    createEllipse: () => editor.createEllipse(),
    createPath: (path) => editor.createPath(path),
    createGroup: () => editor.createGroup(),
    makeColorFill: (color) => editor.makeColorFill(color)
  };
}

/** Resolve the artboard clones are appended to, or null when the target page has none. */
export function resolveTargetArtboard(targetPage: TargetPageLike): TargetArtboard | null {
  return targetPage.artboards?.first ?? null;
}

/**
 * Build the `cloneInto(source)` function applyLayout calls. The factories and artboard are resolved
 * once here; each call delegates to the pure cloneNode. Returns null for every source when the
 * target page has no artboard (so those ids land in applyLayout's missing[]).
 */
export function makeCloneInto(
  editor: AdapterEditorLike,
  targetPage: TargetPageLike
): (source: CloneSourceNode) => PlacedNode | null {
  const factories = buildNodeFactories(editor);
  const artboard = resolveTargetArtboard(targetPage);
  return (source: CloneSourceNode) => {
    if (!artboard) {
      return null;
    }
    return cloneNode(source, factories, artboard);
  };
}
