// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Scene, SemanticRole } from "../src/types/scene";
import { RoleEditor } from "../src/ui/RoleEditor";

function sceneWithRoles(roles: SemanticRole[]): Scene {
  return {
    schemaVersion: "1.0.0",
    canvas: { width: 1000, height: 1000 },
    elements: roles.map((role, index) => ({
      id: `el-${index}`,
      type: "shape",
      semanticRole: role,
      parentId: null,
      x: 0,
      y: 0,
      width: 0.1,
      height: 0.1,
      rotation: 0,
      zIndex: index,
      visible: true,
      optional: false,
      visual: { opacity: 1, luminance: 0.5, colorCoverage: 1 },
      constraints: {},
      readingOrder: null,
      groupAffinities: []
    }))
  };
}

describe("RoleEditor", () => {
  it("tallies each semantic role and the element count", () => {
    render(<RoleEditor scene={sceneWithRoles(["headline", "body", "body"])} />);
    expect(screen.getByText("3 elements")).toBeInTheDocument();
    const headline = screen.getByText("headline").closest(".ld-chip");
    const body = screen.getByText("body").closest(".ld-chip");
    expect(headline).toHaveTextContent("1");
    expect(body).toHaveTextContent("2");
  });

  it("shows a prompt and zero count when there is no scene", () => {
    render(<RoleEditor scene={null} />);
    expect(screen.getByText("0 elements")).toBeInTheDocument();
    expect(screen.getByText("Analyze to inspect semantic roles.")).toBeInTheDocument();
  });
});
