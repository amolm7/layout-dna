import type { Color } from "../types/scene";

/**
 * Reconstruct-via-factories cloning for the Adobe Express Document Sandbox.
 *
 * The Document Sandbox exposes NO node clone/duplicate API (verified against developer.adobe.com:
 * nodes have only `removeFromParent`). The documented way to reproduce content is to create a new
 * node with an Editor factory (`editor.createText(...)`, `createRectangle()`, ...) and append it to
 * a container's `children` list. This module does exactly that, behind an injected `NodeFactories`
 * interface so the mapping is PURE and unit-testable with fakes.
 *
 * Honesty rails (AGENTS.md): the factory names mirrored here match Adobe's published Document API
 * reference (see per-member notes below), but this path is IMPLEMENTED-BUT-UNVERIFIED against live
 * Adobe Express — the tests exercise it with fakes only. In particular, live-node property
 * WRITABILITY is not guaranteed here: `rotation` is read-only on live nodes (set via
 * `setRotationInParent`), and reading a source node's fill color is not a documented shape. Both
 * are abstracted behind the interfaces below and labeled.
 *
 * Boundary: `cloneNode` does create + append + copy-identity (content, translation, rotation,
 * opacity, fill). It does NOT do final positioning — `applyLayout` applies the solved box geometry
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
  /** SVG path string for path nodes (readable `PathNode.path`); required to recreate a path. */
  path?: string;
  /**
   * Source fill. `node.fill` is a documented readable/writable property, but the `Fill` interface's
   * fields are NOT documented — the `{ color }` shape here is assumed and unverified against live
   * Express, so fill-color copying may no-op on the live path (leaving the factory default fill).
   */
  fill?: { color?: Color };
}

/** A node we created on the target and may position later (what `applyLayout` repositions). */
export interface PlacedNode {
  id?: string;
  width?: number;
  height?: number;
  translation?: { x: number; y: number };
  rotation?: number;
  opacity?: number;
  /** Opaque Fill value as produced by `makeColorFill`; set via the documented `node.fill` setter. */
  fill?: unknown;
}

/**
 * The subset of Editor factories reconstruction needs. Names/signatures mirror Adobe's Editor
 * reference:
 * - `createText(textContent): StandaloneTextNode`
 * - `createRectangle(): RectangleNode` (no args; default black fill)
 * - `createEllipse(): EllipseNode` (no args; default black fill)
 * - `createPath(path: string): PathNode` (SVG path string; throws on empty/invalid)
 * - `makeColorFill(color): ColorFill`
 * Return types are narrowed to the writable shape we touch here.
 */
export interface NodeFactories {
  createText(textContent: string): PlacedNode;
  createRectangle(): PlacedNode;
  createEllipse(): PlacedNode;
  createPath(path: string): PlacedNode;
  makeColorFill(color: Color): unknown;
}

/** A container (artboard) whose `children` list accepts appended nodes, per `children.append(node)`. */
export interface TargetArtboard {
  children: { append(node: PlacedNode): void };
}

function nodeType(source: CloneSourceNode): string {
  // Mirrors extractScene's tolerant check; the exact SceneNodeType enum values are unverified here.
  return (source.type ?? "").toLowerCase();
}

function isTextNode(source: CloneSourceNode): boolean {
  return nodeType(source).includes("text");
}

function copyIdentity(source: CloneSourceNode, clone: PlacedNode): void {
  if (source.translation) {
    clone.translation = { x: source.translation.x, y: source.translation.y };
  }
  // NOTE: rotation is read-only on live nodes (set via setRotationInParent). We write it on our
  // writable interface for the pure mapping; the live adapter will need the setter (unverified).
  if (typeof source.rotation === "number") {
    clone.rotation = source.rotation;
  }
  if (typeof source.opacity === "number") {
    clone.opacity = source.opacity;
  }
}

function copyFill(source: CloneSourceNode, factories: NodeFactories, clone: PlacedNode): void {
  const color = source.fill?.color;
  if (color) {
    // makeColorFill + the node.fill setter are documented; reading source.fill.color is not, so
    // this path is exercised by fakes and may no-op on live Express (leaving the default fill).
    clone.fill = factories.makeColorFill(color);
  }
}

/** Create the matching shape node for a shape source, or null when it is not a shape we recreate. */
function createShape(source: CloneSourceNode, factories: NodeFactories): PlacedNode | null {
  const type = nodeType(source);
  if (type.includes("rectangle")) {
    return factories.createRectangle();
  }
  if (type.includes("ellipse")) {
    return factories.createEllipse();
  }
  if (type.includes("path")) {
    // createPath requires a valid SVG path string; without the source's path geometry we cannot
    // recreate it, so it is honestly reported as missing rather than faked with a placeholder shape.
    const path = source.path;
    return typeof path === "string" && path.length > 0 ? factories.createPath(path) : null;
  }
  return null;
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

  const shape = createShape(source, factories);
  if (shape) {
    copyIdentity(source, shape);
    copyFill(source, factories, shape);
    targetArtboard.children.append(shape);
    return shape;
  }

  // IMAGE: returns null — faithfully recreating an image needs the original media/asset (bitmap)
  // via createImageContainer(bitmapData); the source bounds alone cannot reproduce the pixels.
  // GROUP: returns null — needs recursive child reconstruction (createGroup + cloneNode each child
  // into the group). Both are deferred to increment 3 or stay honestly-null.
  return null;
}
