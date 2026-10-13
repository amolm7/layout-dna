"""Self-contained evaluation harness for the deterministic reflow solver.

This package measures the solver's geometric behavior over the example scenes
across a fixed matrix of target canvases. It reports hard-constraint violation
counts, per-gene drift, determinism, and runtime. Drift here is a geometric
proxy for structural change, not a perceptual or aesthetic quality measure.
"""

from .harness import run_evaluation
from .metrics import count_violations
from .targets import TARGETS, Target

__all__ = ["TARGETS", "Target", "count_violations", "run_evaluation"]
