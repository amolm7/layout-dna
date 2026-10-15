import { useEffect, useMemo, useState } from "react";

import { SolverClient } from "../api/solverClient";
import type { FingerprintResponse, GeneName, OptimizeResponse } from "../types/scene";
import { DESIGNS } from "./designs";
import { DesignPicker } from "./DesignPicker";
import { DnaRadar } from "./DnaRadar";
import { RoleEditor } from "./RoleEditor";
import { ScenePreview } from "./ScenePreview";
import { droppedElements, placeScene, placeTarget } from "./scenePlacement";
import { TARGETS, TargetPicker } from "./TargetPicker";
import "./styles.css";

const GENE_LABELS: Array<[GeneName, string]> = [
  ["visualMass", "Visual mass"],
  ["hierarchy", "Hierarchy"],
  ["readingPath", "Reading path"],
  ["alignment", "Alignment"],
  ["negativeSpace", "Negative space"],
  ["grouping", "Grouping"]
];

export default function App() {
  const solver = useMemo(() => new SolverClient(), []);
  const [design, setDesign] = useState(DESIGNS[0]!);
  const [target, setTarget] = useState(TARGETS[2]!);
  const [online, setOnline] = useState<boolean | null>(null);
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Re-run the engine whenever the source design or target format changes.
  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    setError(null);
    void (async () => {
      const healthy = await solver.health();
      if (cancelled) return;
      setOnline(healthy);
      if (!healthy) {
        setFingerprint(null);
        setResult(null);
        setBusy(false);
        return;
      }
      try {
        const [print, optimized] = await Promise.all([
          solver.fingerprint(design.scene),
          solver.optimize(design.scene, target.width, target.height)
        ]);
        if (cancelled) return;
        setFingerprint(print);
        setResult(optimized);
      } catch (cause) {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : "The solver request failed.");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [solver, design, target]);

  const sourcePlaced = useMemo(() => placeScene(design.scene), [design]);
  const targetPlaced = result ? placeTarget(design.scene, result.boxes) : null;
  const dropped = result ? droppedElements(design.scene, result.boxes) : [];

  return (
    <main className="ld-app">
      <header className="ld-header">
        <div className="ld-mark" aria-hidden="true">
          LD
        </div>
        <div className="ld-headings">
          <h1>LayoutDNA</h1>
          <p>Re-lay-out a design for a new canvas instead of stretching or cropping it.</p>
        </div>
        <div
          className={`ld-status ld-status--${online === null ? "pending" : online ? "on" : "off"}`}
          role="status"
          aria-live="polite"
        >
          <span className="ld-status-dot" aria-hidden="true" />
          {online === null ? "Checking engine" : online ? "Engine online" : "Engine offline"}
        </div>
      </header>

      <section className="ld-controls" aria-label="Re-layout inputs">
        <DesignPicker designs={DESIGNS} selected={design} onSelect={setDesign} />
        <TargetPicker selected={target} onSelect={setTarget} />
      </section>

      {online === false && (
        <p className="ld-note" role="note">
          Start the local solver to run the engine: <code>./scripts/dev.sh</code> or run uvicorn on
          port 8000. The source design is shown below in the meantime.
        </p>
      )}
      {error && (
        <p className="ld-note ld-note--error" role="alert">
          {error}
        </p>
      )}

      <section className="ld-stage" aria-label="Before and after">
        <article className="ld-panel">
          <div className="ld-panel-head">
            <h2>Source</h2>
            <span className="ld-dims">
              {design.scene.canvas.width} x {design.scene.canvas.height}
            </span>
          </div>
          <ScenePreview canvas={design.scene.canvas} placed={sourcePlaced} badge="Source" />
        </article>

        <div className="ld-connector" aria-hidden="true">
          <span className="ld-connector-line" />
          <span className="ld-connector-badge">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h13" />
              <path d="m12 6 6 6-6 6" />
            </svg>
          </span>
          <span className="ld-connector-line" />
        </div>

        <article className="ld-panel" aria-busy={busy}>
          <div className="ld-panel-head">
            <h2>Re-layout</h2>
            <span className="ld-dims">
              {target.width} x {target.height}
            </span>
          </div>
          {targetPlaced ? (
            <ScenePreview
              canvas={{ ...result!.target, width: target.width, height: target.height }}
              placed={targetPlaced}
              badge={`${target.width} x ${target.height}`}
            />
          ) : busy ? (
            <div className="ld-skeleton" aria-hidden="true">
              <span className="ld-skel-block" />
              <span className="ld-skel-line" />
              <span className="ld-skel-line ld-skel-line--short" />
            </div>
          ) : (
            <div className="ld-empty">Awaiting engine.</div>
          )}
        </article>
      </section>

      <section className="ld-readouts">
        <DnaRadar fingerprint={fingerprint} />

        <div className="ld-card">
          <div className="ld-card-head">
            <h2>Gene drift</h2>
            <span className="ld-hint">lower is more faithful</span>
          </div>
          {result ? (
            <ul className="ld-drift">
              {GENE_LABELS.map(([gene, label]) => {
                const drift = result.geneDrift[gene];
                return (
                  <li key={gene}>
                    <span className="ld-drift-label">{label}</span>
                    <span className="ld-drift-bar" aria-hidden="true">
                      <span style={{ width: `${Math.min(100, drift * 100)}%` }} />
                    </span>
                    <span className="ld-drift-value">{Math.round(drift * 100)}</span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="ld-muted">Run the engine to measure how each gene shifted.</p>
          )}
        </div>

        <RoleEditor scene={design.scene} />

        <div className="ld-card">
          <div className="ld-card-head">
            <h2>What the engine did</h2>
          </div>
          {result ? (
            <ol className="ld-trace">
              {result.explanation.map((step, index) => (
                <li key={`${step.code}-${index}`}>{step.message}</li>
              ))}
              {dropped.length > 0 && (
                <li className="ld-trace-drop">
                  Dropped {dropped.length} optional element{dropped.length > 1 ? "s" : ""} that
                  could not fit: {dropped.map((element) => element.semanticRole).join(", ")}.
                </li>
              )}
            </ol>
          ) : (
            <p className="ld-muted">The engine explains every move it makes.</p>
          )}
        </div>
      </section>

      <footer className="ld-footer">
        Deterministic, role-aware reflow engine. Scene schema {design.scene.schemaVersion}.
      </footer>
    </main>
  );
}
