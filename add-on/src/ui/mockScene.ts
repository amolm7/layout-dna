import type { DocumentSandboxApi, ElementBox, Scene } from "../types/scene";

export const mockScene: Scene = {
  schemaVersion: "1.0.0",
  canvas: { width: 1080, height: 1350 },
  elements: [
    {
      id: "hero",
      type: "image",
      semanticRole: "hero",
      parentId: null,
      x: 0.08,
      y: 0.08,
      width: 0.84,
      height: 0.48,
      rotation: 0,
      zIndex: 0,
      visible: true,
      optional: false,
      visual: { opacity: 1, luminance: 0.48, colorCoverage: 1 },
      constraints: { fixedAspectRatio: true, mandatoryOnCanvas: true },
      readingOrder: 1,
      groupAffinities: ["story"]
    },
    {
      id: "headline",
      type: "text",
      semanticRole: "headline",
      parentId: null,
      x: 0.08,
      y: 0.61,
      width: 0.68,
      height: 0.13,
      rotation: 0,
      zIndex: 1,
      visible: true,
      optional: false,
      text: { content: "A city in motion", fontSize: 86, fontWeight: 700 },
      visual: { opacity: 1, luminance: 0.08, colorCoverage: 0.65 },
      constraints: { mandatoryOnCanvas: true },
      readingOrder: 0,
      groupAffinities: ["story"]
    },
    {
      id: "logo",
      type: "shape",
      semanticRole: "logo",
      parentId: null,
      x: 0.78,
      y: 0.88,
      width: 0.14,
      height: 0.05,
      rotation: 0,
      zIndex: 2,
      visible: true,
      optional: false,
      visual: { opacity: 1, luminance: 0.1, colorCoverage: 1 },
      constraints: { fixedAspectRatio: true, logoClearSpace: 0.02, mandatoryOnCanvas: true },
      readingOrder: 2,
      groupAffinities: ["brand"]
    }
  ]
};

export const mockDocumentApi: DocumentSandboxApi = {
  extractScene: () => structuredClone(mockScene),
  createOrSelectTargetPage: () => ({ pageId: "mock-target-page", created: true }),
  applyLayout: (boxes: ElementBox[]) => ({ applied: boxes.map((box) => box.id), missing: [] })
};
