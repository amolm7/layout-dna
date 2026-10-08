import type { Scene } from "../types/scene";

export function RoleEditor({ scene }: { scene: Scene | null }) {
  const roles = scene?.elements.reduce<Record<string, number>>((counts, element) => {
    counts[element.semanticRole] = (counts[element.semanticRole] ?? 0) + 1;
    return counts;
  }, {});
  return (
    <section className="card compact">
      <div className="section-heading">
        <h2>Roles</h2>
        <span>{scene?.elements.length ?? 0} elements</span>
      </div>
      <div className="chips">
        {roles ? (
          Object.entries(roles).map(([role, count]) => (
            <span className="chip" key={role}>
              {role}
              <span className="chip-count">{count}</span>
            </span>
          ))
        ) : (
          <span className="muted">Analyze to inspect semantic roles.</span>
        )}
      </div>
    </section>
  );
}
