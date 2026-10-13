"""Run the solver over every example scene x the target matrix.

``run_evaluation`` loads each ``examples/*.json`` scene, reflows it into every
target in :data:`evaluation.targets.TARGETS`, and returns a structured report of
drift, hard-constraint violations, determinism, and runtime. This is measurement
plumbing only; the ``disclaimer`` field states what the drift numbers are not.
"""

from __future__ import annotations

import math
from pathlib import Path
from statistics import mean
from time import perf_counter

from optimize import optimize_scene
from schemas import OptimizeRequest, OptimizeResponse, Scene

from .feasibility import aspect_stress, feasible_expected
from .metrics import count_violations
from .targets import TARGETS, Target

EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

DISCLAIMER = (
    "Gene drift is a geometric proxy for how much a layout's structure moved; "
    "it is not a perceptual or aesthetic quality measure. A clean run means the "
    "solver honored the hard constraints, not that the result looks good."
)


def _load_scenes() -> list[tuple[str, Scene]]:
    scenes = []
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        scenes.append((path.stem, Scene.model_validate_json(path.read_text())))
    return scenes


def _dropped_ids(response: OptimizeResponse) -> list[str]:
    for step in response.explanation:
        if step.code == "optional-removed":
            raw = str(step.metrics.get("droppedIds", "")).strip()
            return [part for part in (p.strip() for p in raw.split(",")) if part]
    return []


def _collisions_resolved(response: OptimizeResponse) -> int:
    for step in response.explanation:
        if step.code == "collisions-resolved":
            return int(step.metrics.get("collisionsResolved", 0))
    return 0


def _run_case(scene_name: str, scene: Scene, target: Target, margin: float) -> dict:
    request = OptimizeRequest(
        scene=scene,
        targetWidth=target.width,
        targetHeight=target.height,
        margin=margin,
    )
    start = perf_counter()
    response = optimize_scene(request)
    runtime_ms = (perf_counter() - start) * 1000
    # A second run with identical input must produce an identical response.
    deterministic = optimize_scene(request) == response

    gene_drift = dict(response.geneDrift)
    violations = count_violations(scene, request, response)
    return {
        "scene": scene_name,
        "target": target.name,
        "targetWidth": target.width,
        "targetHeight": target.height,
        "aspectStress": round(aspect_stress(scene, target), 4),
        "feasibleExpected": feasible_expected(scene, target),
        "geneDrift": gene_drift,
        "aggregateDrift": round(mean(gene_drift.values()), 4),
        "violations": violations,
        "deterministic": deterministic,
        "dropped": _dropped_ids(response),
        "collisionsResolved": _collisions_resolved(response),
        "runtimeMs": round(runtime_ms, 4),
    }


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile of ``values`` for ``pct`` in [0, 100] (empty -> 0.0)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def runtime_summary(runtimes: list[float]) -> dict:
    """Aggregate per-case runtimes into min/mean/p50/p95/max (milliseconds).

    These are measured wall-clock timings, not deterministic values; they are
    reported to show the solver's speed envelope, never gated.
    """
    if not runtimes:
        return {"minMs": 0.0, "meanMs": 0.0, "p50Ms": 0.0, "p95Ms": 0.0, "maxMs": 0.0}
    return {
        "minMs": round(min(runtimes), 4),
        "meanMs": round(mean(runtimes), 4),
        "p50Ms": round(percentile(runtimes, 50), 4),
        "p95Ms": round(percentile(runtimes, 95), 4),
        "maxMs": round(max(runtimes), 4),
    }


def run_evaluation(margin: float = 0.04) -> dict:
    """Evaluate the solver over all example scenes and targets.

    Returns a report dict: ``solverKind``, ``disclaimer``, a ``cases`` list (one
    per scene x target), and a ``summary`` aggregating the cases.
    """
    cases = [
        _run_case(name, scene, target, margin)
        for name, scene in _load_scenes()
        for target in TARGETS
    ]

    aggregate_drifts = [c["aggregateDrift"] for c in cases]
    summary = {
        "cases": len(cases),
        "totalViolations": sum(c["violations"]["total"] for c in cases),
        "meanAggregateDrift": round(mean(aggregate_drifts), 4) if aggregate_drifts else 0.0,
        "maxAggregateDrift": max(aggregate_drifts) if aggregate_drifts else 0.0,
        "allDeterministic": all(c["deterministic"] for c in cases),
        "runtime": runtime_summary([c["runtimeMs"] for c in cases]),
    }

    return {
        "solverKind": "deterministic-reflow",
        "disclaimer": DISCLAIMER,
        "cases": cases,
        "summary": summary,
    }
