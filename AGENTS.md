# LayoutDNA project conventions

- Preserve the iframe/document-sandbox boundary. Network and browser work belongs in the iframe; document traversal and edits belong in the sandbox.
- Keep all Adobe API access behind the document adapter in `add-on/src/documentSandbox/`.
- Maintain matching TypeScript, Python, and JSON Schema scene contracts. Bump `schemaVersion` deliberately when compatibility changes.
- Add or update tests for every behavior change.
- Never fabricate evaluation results. Label placeholders, simulations, and unvalidated metrics clearly.
- Keep generated-layout explanations grounded in recorded solver metrics and transformations.
- Never silently hide mandatory design elements. Optional-element removal must be explicit in the explanation trace.
- Prefer creating a new target page instead of destructively modifying the source page.
- Keep the placeholder solver deterministic; seed any future stochastic behavior and expose the seed.
- Do not add heavyweight optimizer dependencies to the default install until they power an implemented path.

