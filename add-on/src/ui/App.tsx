import { useEffect, useMemo, useState } from "react";

import { SolverClient } from "../api/solverClient";
import type {
  DocumentSandboxApi,
  FingerprintResponse,
  OptimizeResponse,
  Scene,
  TargetSize
} from "../types/scene";
import { DnaRadar } from "./DnaRadar";
import { connectDocument } from "./documentClient";
import { RoleEditor } from "./RoleEditor";
import { TARGETS, TargetPicker } from "./TargetPicker";
import { TransportOverlay } from "./TransportOverlay";
import "./styles.css";

export default function App() {
  const solver = useMemo(() => new SolverClient(), []);
  const [documentApi, setDocumentApi] = useState<DocumentSandboxApi | null>(null);
  const [mode, setMode] = useState<"connecting" | "adobe" | "mock">("connecting");
  const [connected, setConnected] = useState(false);
  const [target, setTarget] = useState<TargetSize>(TARGETS[0]!);
  const [scene, setScene] = useState<Scene | null>(null);
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [status, setStatus] = useState("Ready to analyze");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void Promise.all([connectDocument(), solver.health()]).then(([document, healthy]) => {
      setDocumentApi(document.api);
      setMode(document.mode);
      setConnected(healthy);
    });
  }, [solver]);

  async function analyze() {
    if (!documentApi) return;
    setBusy(true);
    try {
      const nextScene = await documentApi.extractScene();
      setScene(nextScene);
      setFingerprint(await solver.fingerprint(nextScene));
      setStatus(`Analyzed ${nextScene.elements.length} elements`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function generate() {
    if (!documentApi) return;
    setBusy(true);
    try {
      const source = scene ?? (await documentApi.extractScene());
      const optimized = await solver.optimize(source, target.width, target.height);
      setScene(source);
      setResult(optimized);
      await documentApi.createOrSelectTargetPage(target.width, target.height);
      const applied = await documentApi.applyLayout(optimized.boxes, target.width, target.height);
      setStatus(
        applied.missing.length
          ? `Target created; ${applied.missing.length} elements await source-page cloning`
          : `Generated ${target.name} layout`
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <header className="brand-header">
        <div className="mark" aria-hidden="true">
          LD
        </div>
        <div>
          <h1>LayoutDNA</h1>
          <p>Preserve the idea, not just the pixels.</p>
        </div>
      </header>

      <div className="status-row" role="status" aria-live="polite">
        <span className={connected ? "status-dot online" : "status-dot"} aria-hidden="true" />
        <span>{connected ? "Solver connected" : "Solver offline"}</span>
        <span className={mode === "mock" ? "mode-pill is-mock" : "mode-pill"}>
          {mode === "adobe" ? "Adobe document" : "Mock mode"}
        </span>
      </div>

      {mode === "mock" && (
        <aside className="mock-banner" role="note">
          <strong>Mock mode</strong>
          <span>Adobe document access is unavailable. Using a fixture scene.</span>
        </aside>
      )}

      <TargetPicker selected={target} onSelect={setTarget} />

      <div className="actions">
        <button
          className="secondary"
          disabled={busy || !documentApi || !connected}
          aria-busy={busy}
          onClick={analyze}
        >
          Analyze
        </button>
        <button
          className="primary"
          disabled={busy || !documentApi || !connected}
          aria-busy={busy}
          onClick={generate}
        >
          Generate layout
        </button>
      </div>

      <p
        className={busy ? "operation-status is-busy" : "operation-status"}
        role="status"
        aria-live="polite"
      >
        {busy ? "Working…" : status}
      </p>
      <DnaRadar fingerprint={fingerprint} />
      <RoleEditor scene={scene} />
      <TransportOverlay result={result} />
      <footer>Deterministic prototype · schema 1.0.0</footer>
    </main>
  );
}
