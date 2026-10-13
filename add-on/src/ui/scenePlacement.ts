import type { Color, ElementBox, Scene, SceneElement } from "../types/scene";

/** An element resolved to a normalized rectangle for rendering. */
export interface PlacedElement {
  element: SceneElement;
  x: number;
  y: number;
  width: number;
  height: number;
}

const byZIndex = (a: PlacedElement, b: PlacedElement) => a.element.zIndex - b.element.zIndex;

/** Source layout: every element drawn at its own normalized geometry. */
export function placeScene(scene: Scene): PlacedElement[] {
  return scene.elements
    .filter((element) => element.visible)
    .map((element) => ({
      element,
      x: element.x,
      y: element.y,
      width: element.width,
      height: element.height
    }))
    .sort(byZIndex);
}

/**
 * Target layout: solver boxes mapped back onto their source elements. Elements
 * the solver dropped (optional, sacrificed to fit) have no box and are omitted,
 * which is exactly what the re-laid-out canvas should show.
 */
export function placeTarget(scene: Scene, boxes: ElementBox[]): PlacedElement[] {
  const elements = new Map(scene.elements.map((element) => [element.id, element]));
  const placed: PlacedElement[] = [];
  for (const box of boxes) {
    const element = elements.get(box.id);
    if (!element) continue;
    placed.push({ element, x: box.x, y: box.y, width: box.width, height: box.height });
  }
  return placed.sort(byZIndex);
}

/** Elements present in the source but absent from the target (dropped on reflow). */
export function droppedElements(scene: Scene, boxes: ElementBox[]): SceneElement[] {
  const kept = new Set(boxes.map((box) => box.id));
  return scene.elements.filter((element) => element.visible && !kept.has(element.id));
}

export function colorToCss(color: Color | undefined, fallback: string): string {
  if (!color) return fallback;
  const channel = (value: number) => Math.round(Math.max(0, Math.min(1, value)) * 255);
  return `rgba(${channel(color.r)}, ${channel(color.g)}, ${channel(color.b)}, ${color.a})`;
}

/** Perceived luminance of a background, used to pick legible foreground ink. */
export function isDarkBackground(color: Color | undefined): boolean {
  if (!color) return false;
  const luminance = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b;
  return luminance < 0.5;
}
