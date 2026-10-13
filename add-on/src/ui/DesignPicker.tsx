import type { Design } from "./designs";

export function DesignPicker({
  designs,
  selected,
  onSelect
}: {
  designs: Design[];
  selected: Design;
  onSelect: (design: Design) => void;
}) {
  return (
    <fieldset className="ld-field">
      <legend>Source design</legend>
      <div className="ld-option-grid">
        {designs.map((design) => (
          <button
            key={design.id}
            type="button"
            className={design.id === selected.id ? "ld-option is-active" : "ld-option"}
            aria-pressed={design.id === selected.id}
            onClick={() => onSelect(design)}
          >
            <span className="ld-option-name">{design.name}</span>
            <small className="ld-option-note">{design.note}</small>
          </button>
        ))}
      </div>
    </fieldset>
  );
}
