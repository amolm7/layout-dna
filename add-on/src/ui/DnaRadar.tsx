import type { FingerprintResponse, GeneName } from "../types/scene";

const GENES: Array<[GeneName, string]> = [
  ["visualMass", "Mass"],
  ["hierarchy", "Hierarchy"],
  ["readingPath", "Reading"],
  ["alignment", "Alignment"],
  ["negativeSpace", "Space"],
  ["grouping", "Grouping"]
];

const CENTER = 70;
const OUTER = 56;
const RING_RADII = [OUTER, OUTER * (2 / 3), OUTER * (1 / 3)];

function vertex(index: number, radius: number): [number, number] {
  const angle = (Math.PI * 2 * index) / GENES.length - Math.PI / 2;
  return [CENTER + Math.cos(angle) * radius, CENTER + Math.sin(angle) * radius];
}

function ringPoints(radius: number): string {
  return GENES.map((_, index) => vertex(index, radius).join(",")).join(" ");
}

export function DnaRadar({ fingerprint }: { fingerprint: FingerprintResponse | null }) {
  const scores = fingerprint?.scores;
  const points = GENES.map(([key], index) => {
    const angle = (Math.PI * 2 * index) / GENES.length - Math.PI / 2;
    const radius = 52 * (scores?.[key] ?? 0.58);
    return `${70 + Math.cos(angle) * radius},${70 + Math.sin(angle) * radius}`;
  }).join(" ");

  return (
    <section className="ld-card ld-fingerprint">
      <div className="ld-card-head">
        <div>
          <h2>Design fingerprint</h2>
          <p className="ld-hint">{fingerprint ? "Measured proxy" : "Preview"}</p>
        </div>
        <span className="ld-tag">Approx.</span>
      </div>
      <div className="ld-radar">
        <svg
          viewBox="0 0 140 140"
          role="img"
          aria-label="Approximate six-gene design fingerprint radar. Values listed alongside."
        >
          {RING_RADII.map((radius) => (
            <polygon key={radius} className="ld-radar-grid" points={ringPoints(radius)} />
          ))}
          {GENES.map((_, index) => {
            const [x, y] = vertex(index, OUTER);
            return (
              <line key={index} className="ld-radar-spoke" x1={CENTER} y1={CENTER} x2={x} y2={y} />
            );
          })}
          <polygon className="ld-radar-fill" points={points} />
          <circle className="ld-radar-core" cx="70" cy="70" r="3" />
        </svg>
        <div className="ld-gene-list">
          {GENES.map(([key, label]) => (
            <div key={key}>
              <span>{label}</span>
              <strong>{Math.round((scores?.[key] ?? 0.58) * 100)}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
