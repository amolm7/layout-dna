import type { OptimizeResponse } from "../types/scene";

export function TransportOverlay({ result }: { result: OptimizeResponse | null }) {
  if (!result) return null;
  return (
    <section className="card compact">
      <div className="section-heading">
        <h2>Generated geometry</h2>
        <span>{result.boxes.length} boxes</span>
      </div>
      <svg className="transport" viewBox="0 0 100 100" preserveAspectRatio="none">
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
      <p className="trace">{result.explanation[0]?.message}</p>
    </section>
  );
}
