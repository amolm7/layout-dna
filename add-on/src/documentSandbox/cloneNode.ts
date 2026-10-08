/**
 * Reconstruct-via-factories cloning for the Adobe Express Document Sandbox.
 *
 * The Document Sandbox exposes NO node clone/duplicate API (verified against developer.adobe.com:
 * nodes have only `removeFromParent`). The documented way to reproduce content is to create a new
 * node with an Editor factory (`editor.createText(...)`, `createRectangle()`, ...) and append it to
 * a container's `children` list. This module does exactly that, behind an injected `NodeFactories`
 * interface so the mapping is PURE and unit-testable with fakes.
 *
 * Honesty rails (AGENTS.md): the factory names mirrored here (`createText`, text content at
 * `fullContent.text`, `children.append`) match Adobe's published Document API reference, but this
 * path is IMPLEMENTED-BUT-UNVERIFIED against live Adobe Express — the tests exercise it with fakes
 * only. Live-node property writability (translation/rotation/opacity) is therefore not guaranteed
 * here and is abstracted behind the writable-node interface below.
 *
 * Boundary: `cloneNode` does create + append + copy-identity (content, translation, rotation,
 * opacity). It does NOT do final positioning — `applyLayout` applies the solved box geometry
 * (x/y/width/height and rotation) to the node this returns. Keep that split clean.
 */

/** Read-only view of a source node, limited to what reconstruction reads. */
export interface CloneSourceNode {
  id?: string;
  type?: string;
  translation?: { x: number; y: number };
  rotation?: number;
  opacity?: number;
  /** Text nodes expose their string at `fullContent.text`; `allTextContent` is the read-only aggregate. */
  fullContent?: { text?: string };
  allTextContent?: string;
}

/** A node we created on the target and may position later (what `applyLayout` repositions). */
export interface PlacedNode {
  id?: string;
  width?: number;
  height?: number;
  translation?: { x: number; y: number };
  rotation?: number;
  opacity?: number;
}

/**
 * The subset of Editor factories reconstruction needs. Only text is used this increment; later
 * increments extend this with `createRectangle`, `createEllipse`, etc.
 *
 * `createText` mirrors `editor.createText(textContent): StandaloneTextNode` from Adobe's docs.
 */
export interface NodeFactories {
  createText(textContent: string): PlacedNode;
}

/** A container (artboard) whose `children` list accepts appended nodes, per `children.append(node)`. */
export interface TargetArtboard {
  children: { append(node: PlacedNode): void };
}

function isTextNode(source: CloneSourceNode): boolean {
  // Mirrors extractScene's tolerant check; the exact SceneNodeType enum value is unverified here.
  return (source.type ?? "").toLowerCase().includes("text");
}

function copyIdentity(source: CloneSourceNode, clone: PlacedNode): void {
  if (source.translation) {
    clone.translation = { x: source.translation.x, y: source.translation.y };
  }
  if (typeof source.rotation === "number") {
    clone.rotation = source.rotation;
  }
  if (typeof source.opacity === "number") {
    clone.opacity = source.opacity;
  }
}

/**
 * Reconstruct `source` onto `targetArtboard` using `factories`, returning the created node (which
 * `applyLayout` then positions), or null when the type is not yet supported — its id then lands in
 * `applyLayout`'s `missing[]` rather than being silently dropped or faked.
 */
export function cloneNode(
  source: CloneSourceNode,
  factories: NodeFactories,
  targetArtboard: TargetArtboard
): PlacedNode | null {
  if (isTextNode(source)) {
    const content = source.fullContent?.text ?? source.allTextContent ?? "";
    const clone = factories.createText(content);
    copyIdentity(source, clone);
    targetArtboard.children.append(clone);
    return clone;
  }

  // Non-text types (image, shape, group, ...) arrive in later increments.
  return null;
}
