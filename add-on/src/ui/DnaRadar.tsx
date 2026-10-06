import type { FingerprintResponse, GeneName } from "../types/scene";

const GENES: Array<[GeneName, string]> = [
  ["visualMass", "Mass"],
  ["hierarchy", "Hierarchy"],
  ["readingPath", "Reading"],
  ["alignment", "Alignment"],
  ["negativeSpace", "Space"],
  ["grouping", "Grouping"]
];

export function DnaRadar({ fingerprint }: { fingerprint: FingerprintResponse | null }) {
  const scores = fingerprint?.scores;
  const points = GENES.map(([key], index) => {
    const angle = (Math.PI * 2 * index) / GENES.length - Math.PI / 2;
    const radius = 52 * (scores?.[key] ?? 0.58);
    return `${70 + Math.cos(angle) * radius},${70 + Math.sin(angle) * radius}`;
  }).join(" ");

  return (
    <section className="card fingerprint-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Design fingerprint</p>
          <h2>{fingerprint ? "Measured proxy" : "Preview"}</h2>
        </div>
        <span className="approx">Approx.</span>
      </div>
      <div className="radar-wrap">
        <svg viewBox="0 0 140 140" aria-label="Six-gene fingerprint radar">
          <polygon className="radar-grid" points="70,14 118,42 118,98 70,126 22,98 22,42" />
          <polygon className="radar-fill" points={points} />
          <circle cx="70" cy="70" r="3" />
        </svg>
        <div className="gene-list">
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
