import type { ElementBox } from "../types/scene";

interface MutableNodeLike {
  id?: string;
  width?: number;
  height?: number;
  translation?: { x: number; y: number };
  rotation?: number;
  allDescendants?: Iterable<MutableNodeLike>;
}

interface AdobeEditorLike {
  context: {
    currentPage: {
      id: string;
      width: number;
      height: number;
      artboards: { first?: MutableNodeLike };
    };
  };
  documentRoot: {
    pages: {
      addPage(geometry: { width: number; height: number }): { id: string };
    };
  };
}

export function createOrSelectTargetPage(
  editor: AdobeEditorLike,
  width: number,
  height: number
): { pageId: string; created: boolean } {
  // The supported API creates and activates the page. Copying source content is deliberately a
  // separate future adapter capability; this skeleton never resizes the source page in place.
  const page = editor.documentRoot.pages.addPage({ width, height });
  return { pageId: page.id, created: true };
}

export function applyLayout(
  editor: AdobeEditorLike,
  boxes: ElementBox[],
  targetWidth: number,
  targetHeight: number
): { applied: string[]; missing: string[] } {
  const nodes = Array.from(editor.context.currentPage.artboards.first?.allDescendants ?? []);
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const applied: string[] = [];
  const missing: string[] = [];

  for (const box of boxes) {
    const node = byId.get(box.id);
    if (!node) {
      missing.push(box.id);
      continue;
    }
    node.width = box.width * targetWidth;
    node.height = box.height * targetHeight;
    node.translation = { x: box.x * targetWidth, y: box.y * targetHeight };
    node.rotation = box.rotation;
    applied.push(box.id);
  }
  return { applied, missing };
}
