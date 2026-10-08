import type { ElementBox } from "../types/scene";

/**
 * Read-only view of a source node. `applyLayout` never writes to these, so the source page is
 * left untouched (AGENTS.md: prefer creating a new target page over destructively editing source).
 */
interface SourceNodeLike {
  id?: string;
  width?: number;
  height?: number;
  translation?: { x: number; y: number };
  rotation?: number;
  allDescendants?: Iterable<SourceNodeLike>;
}

/** A placed clone on the target page that we reposition to the solved box. */
interface PlacedNodeLike {
  id?: string;
  width?: number;
  height?: number;
  translation?: { x: number; y: number };
  rotation?: number;
}

interface TargetPageLike {
  id: string;
}

interface AddPageEditorLike {
  context: {
    currentPage: {
      id: string;
      width: number;
      height: number;
      artboards: { first?: SourceNodeLike };
    };
  };
  documentRoot: {
    pages: {
      addPage(geometry: { width: number; height: number }): { id: string };
    };
  };
}

/**
 * Editor surface `applyLayout` needs to populate a target page WITHOUT mutating the source.
 *
 * `cloneInto` is a clearly-labeled PLACEHOLDER adapter capability. As of the Adobe Express
 * Document Sandbox API (verified against developer.adobe.com, Oct 2026) there is no public node
 * clone/duplicate method — only `removeFromParent`, with content built via `editor.createX()`
 * factories appended to a parent's `children` list. The real adapter must therefore reconstruct
 * each node on the target artboard and copy its properties; it is intentionally injected here so
 * this module never fabricates an Adobe API that does not exist. Tests inject a working fake.
 * A clone that cannot be produced returns null/undefined (or throws), and its id is reported in
 * `missing[]` rather than silently dropped.
 */
interface CloningEditorLike {
  sourcePage: { artboards: { first?: SourceNodeLike } };
  targetPage: TargetPageLike;
  cloneInto(node: SourceNodeLike, targetPage: TargetPageLike): PlacedNodeLike | null | undefined;
}

export function createOrSelectTargetPage(
  editor: AddPageEditorLike,
  width: number,
  height: number
): { pageId: string; created: boolean } {
  // The supported API creates and activates the page. Source content is cloned onto it separately
  // by `applyLayout`; this call never resizes the source page in place.
  const page = editor.documentRoot.pages.addPage({ width, height });
  return { pageId: page.id, created: true };
}

export function applyLayout(
  editor: CloningEditorLike,
  boxes: ElementBox[],
  targetWidth: number,
  targetHeight: number
): { applied: string[]; missing: string[] } {
  const sourceNodes = Array.from(editor.sourcePage.artboards.first?.allDescendants ?? []);
  const sourceById = new Map(sourceNodes.map((node) => [node.id, node]));
  const applied: string[] = [];
  const missing: string[] = [];

  for (const box of boxes) {
    const source = sourceById.get(box.id);
    if (!source) {
      missing.push(box.id);
      continue;
    }

    let clone: PlacedNodeLike | null | undefined;
    try {
      clone = editor.cloneInto(source, editor.targetPage);
    } catch {
      clone = null;
    }
    if (!clone) {
      // Genuinely could not be cloned/placed onto the target page.
      missing.push(box.id);
      continue;
    }

    // Geometry is applied to the CLONE on the target page; the source node is never written to.
    // These writes are wrapped because on live Adobe Express per-type geometry writability is
    // unverified and `rotation` is read-only (it needs setRotationInParent) — a single throwing
    // assignment would otherwise abort the whole loop and lose every remaining element. On a throw
    // we treat this element as not placed and move on. Tradeoff: cloneInto may already have appended
    // the clone, so an un-positioned clone can remain on the target page — an un-positioned clone is
    // preferable to crashing the entire apply and dropping all other elements.
    try {
      clone.width = box.width * targetWidth;
      clone.height = box.height * targetHeight;
      clone.translation = { x: box.x * targetWidth, y: box.y * targetHeight };
      clone.rotation = box.rotation;
      applied.push(box.id);
    } catch {
      missing.push(box.id);
    }
  }

  return { applied, missing };
}
