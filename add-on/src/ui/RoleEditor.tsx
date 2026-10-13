import type { Scene } from "../types/scene";

export function RoleEditor({ scene }: { scene: Scene | null }) {
  const roles = scene?.elements.reduce<Record<string, number>>((counts, element) => {
    counts[element.semanticRole] = (counts[element.semanticRole] ?? 0) + 1;
    return counts;
  }, {});
  return (
    <section className="ld-card">
      <div className="ld-card-head">
        <h2>Roles</h2>
        <span>{scene?.elements.length ?? 0} elements</span>
      </div>
      <div className="ld-chips">
        {roles ? (
          Object.entries(roles).map(([role, count]) => (
            <span className="ld-chip" key={role}>
              {role}
              <span className="ld-chip-count">{count}</span>
            </span>
          ))
        ) : (
          <span className="ld-muted">Analyze to inspect semantic roles.</span>
        )}
      </div>
    </section>
  );
}
