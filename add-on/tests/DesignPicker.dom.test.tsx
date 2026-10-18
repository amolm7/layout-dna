// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DESIGNS } from "../src/ui/designs";
import { DesignPicker } from "../src/ui/DesignPicker";

describe("DesignPicker", () => {
  it("renders a button per design with its name and note", () => {
    render(<DesignPicker designs={DESIGNS} selected={DESIGNS[0]!} onSelect={() => {}} />);
    expect(screen.getAllByRole("button")).toHaveLength(DESIGNS.length);
    for (const design of DESIGNS) {
      expect(screen.getByText(design.name)).toBeInTheDocument();
      expect(screen.getByText(design.note)).toBeInTheDocument();
    }
  });

  it("marks only the selected design as pressed", () => {
    const selected = DESIGNS[1] ?? DESIGNS[0]!;
    render(<DesignPicker designs={DESIGNS} selected={selected} onSelect={() => {}} />);
    const pressed = screen
      .getAllByRole("button")
      .filter((button) => button.getAttribute("aria-pressed") === "true");
    expect(pressed).toHaveLength(1);
    expect(pressed[0]!).toHaveTextContent(selected.name);
  });

  it("calls onSelect with the clicked design", () => {
    const onSelect = vi.fn();
    const target = DESIGNS[DESIGNS.length - 1]!;
    render(<DesignPicker designs={DESIGNS} selected={DESIGNS[0]!} onSelect={onSelect} />);
    fireEvent.click(screen.getByText(target.name));
    expect(onSelect).toHaveBeenCalledWith(target);
  });
});
