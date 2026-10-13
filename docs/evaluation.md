# Evaluation

No quality claims have been measured yet. This file defines the evaluation contract, not results.

## Automated checks

- JSON/Pydantic validity and cross-language fixture compatibility
- deterministic output across repeat runs
- hard-constraint violation counts
- per-gene drift and aggregate weighted loss
- runtime by element count, nesting depth, and target aspect delta

## Running the harness

`solver/evaluation/` implements the automated-checks contract above. It reflows every
`examples/*.json` scene into a fixed matrix of target canvases (`evaluation/targets.py`) and
reports, per case: per-gene drift, an aggregate drift, hard-constraint violation counts
(`evaluation/metrics.py`), determinism, and runtime.

```bash
.venv/bin/python -m evaluation          # human-readable table
.venv/bin/python -m evaluation --json   # full report as JSON
```

The summary also reports a runtime envelope across all cases — `min`, `mean`, `p50`, `p95`,
and `max` milliseconds. These are measured wall-clock timings for the solver's speed profile,
reported but never gated (timing is not deterministic).

The process exits non-zero if any **feasible** scene×target case has a hard-constraint
violation, or if any case is non-deterministic, so it can gate CI.

### Feasibility, not cherry-picking

Some targets are geometrically impossible for a given scene — e.g. a 4:5 poster with a
mandatory fixed-aspect hero cannot inhabit an 8:1 ad banner without breaking a minimum size or
overlapping. The harness does not hide these: it classifies each case by **aspect stress**
(`evaluation/feasibility.py`, the ratio of target to source aspect, ≥ 1) and marks cases above
`ASPECT_STRESS_LIMIT` as `feasibleExpected = false`. Feasible cases are held to zero violations;
infeasible cases are reported as best-effort and excluded from the gate. This is a transparent
geometric heuristic; it is not a claim that feasible results are aesthetically good.

Drift here is a geometric proxy for how much a layout's structure moved — not a perceptual or
aesthetic quality measure. A clean run means the solver honored the hard constraints, nothing
more. No numbers from this harness are committed as empirical quality claims.

## Human study

Use blinded pairwise comparisons between source-aware alternatives: LayoutDNA, uniform scaling, a constraint-only baseline, and a production resize baseline where licensing permits. Ask raters which target better preserves hierarchy, brand identity, reading order, and overall composition. Randomize side and method order.

Report sample composition, exclusions, confidence intervals, and failures. Never convert placeholder scores or demo feedback into empirical claims.

