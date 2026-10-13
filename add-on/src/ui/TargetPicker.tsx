import type { TargetSize } from "../types/scene";

export const TARGETS: TargetSize[] = [
  { name: "Square", width: 1080, height: 1080 },
  { name: "Story", width: 1080, height: 1920 },
  { name: "Landscape", width: 1200, height: 628 },
  { name: "Leaderboard", width: 728, height: 90 }
];

export function TargetPicker({
  selected,
  onSelect
}: {
  selected: TargetSize;
  onSelect: (target: TargetSize) => void;
}) {
  return (
    <fieldset className="ld-field">
      <legend>Target format</legend>
      <div className="ld-option-grid">
        {TARGETS.map((target) => (
          <button
            key={target.name}
            type="button"
            className={target.name === selected.name ? "ld-option is-active" : "ld-option"}
            aria-pressed={target.name === selected.name}
            onClick={() => onSelect(target)}
          >
            <span className="ld-option-name">{target.name}</span>
            <small className="ld-option-note">
              {target.width} x {target.height}
            </small>
          </button>
        ))}
      </div>
    </fieldset>
  );
}
