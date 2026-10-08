import type { OptimizeResponse } from "../types/scene";

export function TransportOverlay({ result }: { result: OptimizeResponse | null }) {
  if (!result) return null;
  const { width, height } = result.target;
  return (
    <section className="card compact">
      <div className="section-heading">
        <h2>Generated geometry</h2>
        <span>{result.boxes.length} boxes</span>
      </div>
      <div className="transport-frame">
        <svg
          className="transport"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          style={{ aspectRatio: `${width} / ${height}` }}
          role="img"
          aria-label={`Generated layout preview for ${width} by ${height}, ${result.boxes.length} boxes`}
        >
          {result.boxes.map((box) => (
            <rect
              key={box.id}
              x={box.x * 100}
              y={box.y * 100}
              width={box.width * 100}
              height={box.height * 100}
              rx="1"
            />
          ))}
        </svg>
      </div>
      <p className="trace">{result.explanation[0]?.message}</p>
    </section>
  );
}
