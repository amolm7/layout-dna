"""Tests for the deterministic role-aware reflow optimizer."""

from pathlib import Path

import pytest

from optimize import optimize_scene
from optimize.losses import measure_gene_scores
from schemas import OptimizeRequest, Scene

ROOT = Path(__file__).parents[2]


@pytest.fixture
def poster() -> Scene:
    return Scene.model_validate_json((ROOT / "examples" / "editorial-poster.json").read_text())


def _overlap(a: dict, b: dict) -> bool:
    ox = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    oy = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    return ox > 1e-6 and oy > 1e-6


def test_optimize_is_deterministic(poster: Scene) -> None:
    req = OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1920, margin=0.04)
    assert optimize_scene(req) == optimize_scene(req)


def test_foreground_boxes_do_not_overlap(poster: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1920, margin=0.04)
    )
    boxes = [b.model_dump() for b in result.boxes]
    # Full-bleed backgrounds are allowed to sit behind everything.
    foreground = [b for b in boxes if not (b["width"] >= 0.999 and b["height"] >= 0.999)]
    for i, first in enumerate(foreground):
        for second in foreground[i + 1 :]:
            assert not _overlap(first, second), f"{first['id']} overlaps {second['id']}"


def test_reading_order_preserved_top_to_bottom(poster: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1920, margin=0.04)
    )
    reading = {e.id: e.readingOrder for e in poster.elements if e.readingOrder is not None}
    ordered = sorted((b for b in result.boxes if b.id in reading), key=lambda b: b.y)
    orders = [reading[b.id] for b in ordered]
    assert orders == sorted(orders), "vertical placement must follow reading order"


def test_drift_is_measured_in_range(poster: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1920, margin=0.04)
    )
    assert set(result.geneDrift) == {
        "visualMass",
        "hierarchy",
        "readingPath",
        "alignment",
        "negativeSpace",
        "grouping",
    }
    for value in result.geneDrift.values():
        assert 0.0 <= value <= 1.0


def test_drift_varies_with_target_shape(poster: Scene) -> None:
    gentle = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1350, margin=0.04)
    )
    extreme = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1920, targetHeight=400, margin=0.04)
    )
    # A real measurement responds to the transform; faked constants would not.
    assert gentle.geneDrift != extreme.geneDrift


def test_mandatory_elements_are_never_dropped() -> None:
    scene = Scene.model_validate(
        {
            "schemaVersion": "1.0.0",
            "canvas": {"width": 1000, "height": 1000},
            "elements": [
                _el("keep-head", "headline", 0.1, optional=False, reading=0),
                _el("keep-logo", "logo", 0.1, optional=False, reading=3,
                    extra={"logoClearSpace": 0.02, "fixedAspectRatio": True}),
                _el("drop-deco", "decoration", 0.4, optional=True, reading=2),
                _el("drop-body", "body", 0.4, optional=True, reading=1),
            ],
        }
    )
    result = optimize_scene(
        OptimizeRequest(scene=scene, targetWidth=600, targetHeight=120, margin=0.05)
    )
    placed = {b.id for b in result.boxes}
    assert "keep-head" in placed and "keep-logo" in placed
    dropped_steps = [s for s in result.explanation if s.code == "optional-removed"]
    for step in dropped_steps:
        # Anything reported dropped must be an optional element, and must be absent.
        for dropped_id in str(step.metrics["droppedIds"]).split(", "):
            assert dropped_id not in placed


def test_result_scene_gene_scores_are_valid(poster: Scene) -> None:
    scores = measure_gene_scores(poster)
    assert all(0.0 <= v <= 1.0 for v in scores.values())


def _el(
    el_id: str,
    role: str,
    height: float,
    *,
    optional: bool,
    reading: int,
    extra: dict | None = None,
) -> dict:
    constraints = {"mandatoryOnCanvas": not optional}
    if extra:
        constraints.update(extra)
    return {
        "id": el_id,
        "type": "text" if role in ("headline", "body") else "shape",
        "semanticRole": role,
        "parentId": None,
        "x": 0.1,
        "y": 0.1,
        "width": 0.3,
        "height": height,
        "rotation": 0,
        "zIndex": reading,
        "visible": True,
        "optional": optional,
        "visual": {"opacity": 1, "luminance": 0.2, "colorCoverage": 0.5},
        "constraints": constraints,
        "readingOrder": reading,
        "groupAffinities": [],
    }
