// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TARGETS, TargetPicker } from "../src/ui/TargetPicker";

describe("TargetPicker", () => {
  it("renders every target with its pixel dimensions", () => {
    render(<TargetPicker selected={TARGETS[0]!} onSelect={() => {}} />);
    for (const target of TARGETS) {
      expect(screen.getByText(target.name)).toBeInTheDocument();
      expect(screen.getByText(`${target.width} x ${target.height}`)).toBeInTheDocument();
    }
  });

  it("marks only the selected target as pressed", () => {
    const selected = TARGETS[1]!;
    render(<TargetPicker selected={selected} onSelect={() => {}} />);
    const pressed = screen
      .getAllByRole("button")
      .filter((button) => button.getAttribute("aria-pressed") === "true");
    expect(pressed).toHaveLength(1);
    expect(pressed[0]!).toHaveTextContent(selected.name);
  });

  it("calls onSelect with the clicked target", () => {
    const onSelect = vi.fn();
    render(<TargetPicker selected={TARGETS[0]!} onSelect={onSelect} />);
    fireEvent.click(screen.getByText(TARGETS[2]!.name));
    expect(onSelect).toHaveBeenCalledWith(TARGETS[2]);
  });
});
