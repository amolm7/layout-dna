"""Run the solver over every example scene x the target matrix.

``run_evaluation`` loads each ``examples/*.json`` scene, reflows it into every
target in :data:`evaluation.targets.TARGETS`, and returns a structured report of
drift, hard-constraint violations, determinism, and runtime. This is measurement
plumbing only; the ``disclaimer`` field states what the drift numbers are not.
"""

from __future__ import annotations

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
    }

    return {
        "solverKind": "deterministic-reflow",
        "disclaimer": DISCLAIMER,
        "cases": cases,
        "summary": summary,
    }
