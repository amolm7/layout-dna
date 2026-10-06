# Evaluation

No quality claims have been measured yet. This file defines the evaluation contract, not results.

## Automated checks

- JSON/Pydantic validity and cross-language fixture compatibility
- deterministic output across repeat runs
- hard-constraint violation counts
- per-gene drift and aggregate weighted loss
- runtime by element count, nesting depth, and target aspect delta

## Human study

Use blinded pairwise comparisons between source-aware alternatives: LayoutDNA, uniform scaling, a constraint-only baseline, and a production resize baseline where licensing permits. Ask raters which target better preserves hierarchy, brand identity, reading order, and overall composition. Randomize side and method order.

Report sample composition, exclusions, confidence intervals, and failures. Never convert placeholder scores or demo feedback into empirical claims.

