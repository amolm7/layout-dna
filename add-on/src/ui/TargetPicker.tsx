import type { TargetSize } from "../types/scene";

export const TARGETS: TargetSize[] = [
  { name: "Square", width: 1080, height: 1080 },
  { name: "Story", width: 1080, height: 1920 },
  { name: "Landscape", width: 1200, height: 628 },
  { name: "728×90", width: 728, height: 90 }
];

export function TargetPicker({
  selected,
  onSelect
}: {
  selected: TargetSize;
  onSelect: (target: TargetSize) => void;
}) {
  return (
    <fieldset className="target-picker">
      <legend>Target format</legend>
      <div className="target-grid">
        {TARGETS.map((target) => (
          <button
            className={target.name === selected.name ? "target active" : "target"}
            key={target.name}
            onClick={() => onSelect(target)}
            type="button"
            aria-pressed={target.name === selected.name}
          >
            <span>{target.name}</span>
            <small>
              {target.width} × {target.height}
            </small>
          </button>
        ))}
      </div>
    </fieldset>
  );
}
