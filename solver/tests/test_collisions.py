"""Tests for deterministic post-placement collision resolution."""

from optimize import optimize_scene
from optimize.reflow import reflow
from schemas import OptimizeRequest, Scene

EPS = 1e-6


def _el(el_id: str, role: str, y: float, h: float, reading: int, *, locked: bool = False) -> dict:
    return {
        "id": el_id,
        "type": "text",
        "semanticRole": role,
        "parentId": None,
        "x": 0.1,
        "y": y,
        "width": 0.5,
        "height": h,
        "rotation": 0,
        "zIndex": reading,
        "visible": True,
        "optional": False,
        "visual": {"opacity": 1, "luminance": 0.2, "colorCoverage": 0.5},
        "constraints": {"mandatoryOnCanvas": True, "lockedPosition": locked},
        "readingOrder": reading,
        "groupAffinities": [],
    }


def _request() -> OptimizeRequest:
    # The locked CTA is pinned mid-canvas (y=0.40) while the flowed headline,
    # body and subhead naturally spread down the column through that same spot.
    scene = Scene.model_validate(
        {
            "schemaVersion": "1.0.0",
            "canvas": {"width": 1000, "height": 1000},
            "elements": [
                _el("head", "headline", 0.05, 0.15, 0),
                _el("sub", "subhead", 0.25, 0.15, 1),
                _el("body", "body", 0.45, 0.15, 2),
                _el("cta", "cta", 0.40, 0.15, 3, locked=True),
            ],
        }
    )
    return OptimizeRequest(scene=scene, targetWidth=1000, targetHeight=1000, margin=0.04)


def _overlap(a, b) -> bool:
    ox = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
    oy = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
    return ox > EPS and oy > EPS


def test_collisions_are_resolved_and_counted() -> None:
    result = reflow(_request())
    assert result.collisions_resolved > 0
    boxes = result.boxes
    for i, first in enumerate(boxes):
        for second in boxes[i + 1 :]:
            assert not _overlap(first, second), f"{first.id} overlaps {second.id}"


def test_locked_element_does_not_move() -> None:
    request = _request()
    result = reflow(request)
    cta = next(b for b in result.boxes if b.id == "cta")
    assert cta.y == 0.40  # pinned at its source y (inside the safe area)
    assert cta.x == 0.1


def test_resolution_is_deterministic() -> None:
    request = _request()
    assert reflow(request) == reflow(request)
    assert optimize_scene(request) == optimize_scene(request)


def test_collision_step_reports_recorded_count() -> None:
    request = _request()
    result = reflow(request)
    response = optimize_scene(request)
    steps = [s for s in response.explanation if s.code == "collisions-resolved"]
    assert len(steps) == 1
    assert steps[0].metrics["collisionsResolved"] == float(result.collisions_resolved)


def test_no_collision_step_when_nothing_overlaps() -> None:
    scene = Scene.model_validate(
        {
            "schemaVersion": "1.0.0",
            "canvas": {"width": 1000, "height": 1000},
            "elements": [_el("head", "headline", 0.1, 0.2, 0), _el("body", "body", 0.5, 0.2, 1)],
        }
    )
    request = OptimizeRequest(scene=scene, targetWidth=1000, targetHeight=1000)
    assert reflow(request).collisions_resolved == 0
    assert all(s.code != "collisions-resolved" for s in optimize_scene(request).explanation)
