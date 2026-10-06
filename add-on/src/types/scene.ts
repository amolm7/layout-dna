export const SCHEMA_VERSION = "1.0.0" as const;

export type ElementType = "text" | "image" | "shape" | "group" | "unknown";
export type SemanticRole =
  | "headline"
  | "subhead"
  | "body"
  | "cta"
  | "logo"
  | "hero"
  | "decoration"
  | "background"
  | "unknown";
export type GeneName =
  "visualMass" | "hierarchy" | "readingPath" | "alignment" | "negativeSpace" | "grouping";

export interface Color {
  r: number;
  g: number;
  b: number;
  a: number;
}

export interface SceneElement {
  id: string;
  type: ElementType;
  semanticRole: SemanticRole;
  parentId: string | null;
  /** Normalized to the source canvas. */
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  zIndex: number;
  visible: boolean;
  optional: boolean;
  text?: {
    content: string;
    fontSize?: number;
    fontWeight?: number;
    lineHeight?: number;
    align?: "left" | "center" | "right" | "justify";
  };
  visual: {
    opacity: number;
    luminance: number;
    colorCoverage: number;
    fill?: Color;
  };
  constraints: {
    minWidth?: number;
    minHeight?: number;
    fixedAspectRatio?: boolean;
    lockedPosition?: boolean;
    logoClearSpace?: number;
    mandatoryOnCanvas?: boolean;
  };
  readingOrder: number | null;
  groupAffinities: string[];
}

export interface Scene {
  schemaVersion: typeof SCHEMA_VERSION;
  canvas: { width: number; height: number; backgroundColor?: Color };
  elements: SceneElement[];
}

export interface ElementBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
}

export interface OptimizeResponse {
  schemaVersion: typeof SCHEMA_VERSION;
  solverKind: "deterministic-placeholder";
  target: { width: number; height: number; backgroundColor?: Color };
  boxes: ElementBox[];
  geneDrift: Record<GeneName, number>;
  explanation: Array<{
    code: string;
    message: string;
    metrics: Record<string, string | number | boolean>;
  }>;
}

export interface FingerprintResponse {
  schemaVersion: typeof SCHEMA_VERSION;
  approximation: true;
  scores: Record<GeneName, number>;
  notes: string[];
}

export interface TargetSize {
  name: string;
  width: number;
  height: number;
}

export interface DocumentSandboxApi {
  extractScene(): Scene;
  createOrSelectTargetPage(width: number, height: number): { pageId: string; created: boolean };
  applyLayout(
    boxes: ElementBox[],
    targetWidth: number,
    targetHeight: number
  ): {
    applied: string[];
    missing: string[];
  };
}
