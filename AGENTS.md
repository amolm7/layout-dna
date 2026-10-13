# LayoutDNA project conventions

- Keep the web client and the solver service decoupled: the client talks to the solver only over the HTTP API, and holds no solver logic of its own.
- The client renders results itself (in-browser SVG). It does not write to any external document or host application.
- Maintain matching TypeScript, Python, and JSON Schema scene contracts. Bump `schemaVersion` deliberately when compatibility changes.
- Add or update tests for every behavior change.
- Never fabricate evaluation results. Label placeholders, simulations, and unvalidated metrics clearly.
- Keep generated-layout explanations grounded in recorded solver metrics and transformations.
- Never silently hide mandatory design elements. Optional-element removal must be explicit in the explanation trace.
- Re-layout is non-destructive: produce a new target layout, never mutate the source scene.
- Keep the solver deterministic; seed any future stochastic behavior and expose the seed.
- Do not add heavyweight optimizer dependencies to the default install until they power an implemented path.

## Commit conventions

- Make small, focused commits — one logical change each, not large batches.
- Write a clear commit message summarizing what changed and why.
- Before pushing, run `git log origin/main..HEAD --oneline --stat` and review the commits going out; confirm before pushing.
- After pushing, confirm what landed.

