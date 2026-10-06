import type { Scene, SceneElement, SemanticRole } from "../types/scene";
import { SCHEMA_VERSION } from "../types/scene";

interface AdobeNodeLike {
  id?: string;
  type?: string;
  name?: string;
  parent?: { id?: string };
  translation?: { x: number; y: number };
  width?: number;
  height?: number;
  rotation?: number;
  opacity?: number;
  allTextContent?: string;
}

interface AdobeEditorLike {
  context: {
    currentPage: {
      width: number;
      height: number;
      artboards: { first?: { allDescendants?: Iterable<AdobeNodeLike> } };
    };
  };
}

function roleFromName(name = ""): SemanticRole {
  const value = name.toLowerCase();
  if (value.includes("logo") || value.includes("brand")) return "logo";
  if (value.includes("headline") || value.includes("title")) return "headline";
  if (value.includes("cta") || value.includes("button")) return "cta";
  if (value.includes("hero")) return "hero";
  return "unknown";
}

function typeFromAdobe(type = ""): SceneElement["type"] {
  const value = type.toLowerCase();
  if (value.includes("text")) return "text";
  if (value.includes("image") || value.includes("media")) return "image";
  if (value.includes("group")) return "group";
  if (value.includes("rectangle") || value.includes("ellipse") || value.includes("path")) {
    return "shape";
  }
  return "unknown";
}

export function extractScene(editor: AdobeEditorLike): Scene {
  const page = editor.context.currentPage;
  const nodes = Array.from(page.artboards.first?.allDescendants ?? []);
  const elements = nodes
    .filter((node) => typeof node.width === "number" && typeof node.height === "number")
    .map((node, zIndex): SceneElement => {
      const x = node.translation?.x ?? 0;
      const y = node.translation?.y ?? 0;
      const width = node.width ?? 0;
      const height = node.height ?? 0;
      const type = typeFromAdobe(node.type);
      return {
        id: node.id ?? `node-${zIndex}`,
        type,
        semanticRole: roleFromName(node.name),
        parentId: node.parent?.id ?? null,
        x: x / page.width,
        y: y / page.height,
        width: width / page.width,
        height: height / page.height,
        rotation: node.rotation ?? 0,
        zIndex,
        visible: (node.opacity ?? 1) > 0,
        optional: false,
        ...(type === "text" ? { text: { content: node.allTextContent ?? "" } } : {}),
        // Adobe's public node bounds/opacity are used here. Luminance and coverage are explicit
        // approximations until fill/media sampling is implemented per node subtype.
        visual: { opacity: node.opacity ?? 1, luminance: 0.5, colorCoverage: 1 },
        constraints: { mandatoryOnCanvas: true },
        readingOrder: zIndex,
        groupAffinities: node.parent?.id ? [node.parent.id] : []
      };
    });

  return {
    schemaVersion: SCHEMA_VERSION,
    canvas: { width: page.width, height: page.height },
    elements
  };
}
