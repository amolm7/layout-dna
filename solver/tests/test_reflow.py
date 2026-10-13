"""Tests for the deterministic role-aware reflow optimizer."""

import json
from pathlib import Path

import pytest

from optimize import optimize_scene
from optimize.losses import measure_gene_scores
from optimize.reflow import detect_unmet, reflow
from schemas import OptimizeRequest, Scene

ROOT = Path(__file__).parents[2]

_TOL = 1e-6


@pytest.fixture
def poster() -> Scene:
    return Scene.model_validate_json((ROOT / "examples" / "editorial-poster.json").read_text())


@pytest.fixture
def card() -> Scene:
    return Scene.model_validate_json((ROOT / "examples" / "nested-group-card.json").read_text())


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


def _within(child: dict, parent, tol: float = 1e-3) -> bool:
    return (
        child["x"] >= parent.x - tol
        and child["y"] >= parent.y - tol
        and child["x"] + child["width"] <= parent.x + parent.width + tol
        and child["y"] + child["height"] <= parent.y + parent.height + tol
    )


def test_nested_group_fixture_matches_schema_and_pydantic() -> None:
    # Pydantic StrictModel (extra=forbid) is the authoritative contract; also
    # check the fixture structurally against scene.schema.json (stdlib only, no
    # jsonschema dependency) so the two stay honest with each other.
    raw = json.loads((ROOT / "examples" / "nested-group-card.json").read_text())
    Scene.model_validate(raw)  # raises on any contract violation

    schema = json.loads((ROOT / "schemas" / "scene.schema.json").read_text())
    element = schema["$defs"]["element"]
    allowed = set(element["properties"])
    required = set(element["required"])
    type_enum = set(element["properties"]["type"]["enum"])
    role_enum = set(element["properties"]["semanticRole"]["enum"])
    constraint_keys = set(element["properties"]["constraints"]["properties"])
    for el in raw["elements"]:
        assert set(el) <= allowed, f"{el['id']} has keys outside the schema"
        assert required <= set(el), f"{el['id']} missing required keys"
        assert el["type"] in type_enum
        assert el["semanticRole"] in role_enum
        assert set(el["constraints"]) <= constraint_keys


def test_group_children_stay_within_parent(card: Scene) -> None:
    req = OptimizeRequest(scene=card, targetWidth=1080, targetHeight=1080, margin=0.04)
    result = reflow(req)
    # Both the top-level group and the nested group get a solved box.
    assert set(result.group_boxes) == {"card", "card-text"}
    parent_of = {e.id: e.parentId for e in card.elements}
    by_id = {b.id: b.model_dump() for b in result.boxes}
    # Every element that lives under a group (leaf or nested group) must stay
    # inside its parent's solved box, so cohesion survives the reflow.
    for element in card.elements:
        parent_id = parent_of[element.id]
        if parent_id is None:
            continue
        box = by_id.get(element.id) or result.group_boxes[element.id].model_dump()
        assert _within(box, result.group_boxes[parent_id]), (
            f"{element.id} escaped group {parent_id}"
        )


def test_group_siblings_keep_reading_order(card: Scene) -> None:
    req = OptimizeRequest(scene=card, targetWidth=1080, targetHeight=1080, margin=0.04)
    boxes = {b.id: b for b in reflow(req).boxes}
    # Within the nested text group, the headline (readingOrder 0) sits above the
    # subhead (readingOrder 1) on the vertical flow axis.
    assert boxes["card-title"].y < boxes["card-sub"].y


def test_no_child_of_mandatory_group_is_dropped(card: Scene) -> None:
    req = OptimizeRequest(scene=card, targetWidth=1080, targetHeight=1920, margin=0.04)
    placed = {b.id for b in optimize_scene(req).boxes}
    # card and card-text are mandatory groups; their leaf descendants must all
    # be placed (group containers are represented by their children, not emitted).
    for child_id in ("card-image", "card-title", "card-sub"):
        assert child_id in placed


def test_grouped_layout_is_deterministic(card: Scene) -> None:
    req = OptimizeRequest(scene=card, targetWidth=1080, targetHeight=1920, margin=0.04)
    assert optimize_scene(req) == optimize_scene(req)
    assert reflow(req) == reflow(req)


def _infeasible_steps(result) -> list:
    return [s for s in result.explanation if s.code == "constraint-infeasible"]


def test_min_size_infeasibility_is_recorded(poster: Scene) -> None:
    # A 728x90 leaderboard cannot host the fixed-aspect hero at its minWidth.
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=728, targetHeight=90, margin=0.04)
    )
    steps = _infeasible_steps(result)
    assert len(steps) == 1
    assert "hero" in str(steps[0].metrics["unmetIds"])
    assert steps[0].metrics["worstKind"] == "minWidth"
    # Never hidden: the element is still placed, just flagged.
    assert "hero" in {b.id for b in result.boxes}


def test_overlap_infeasibility_is_recorded(poster: Scene) -> None:
    # On a 970x250 strip the logo cannot clear the body after margin clamping.
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=970, targetHeight=250, margin=0.04)
    )
    steps = _infeasible_steps(result)
    assert len(steps) == 1
    assert "logo" in str(steps[0].metrics["unmetIds"])
    assert "overlap" in str(steps[0].metrics["kinds"])
    assert "logo" in {b.id for b in result.boxes}


def test_feed_shaped_target_has_no_infeasibility(poster: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1350, margin=0.04)
    )
    assert _infeasible_steps(result) == []
    # solver-scope must remain the final explanation step.
    assert result.explanation[-1].code == "solver-scope"


def test_detect_unmet_is_empty_when_constraints_hold(poster: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=poster, targetWidth=1080, targetHeight=1350, margin=0.04)
    )
    elements_by_id = {e.id: e for e in poster.elements}
    assert detect_unmet(result.boxes, elements_by_id) == []


@pytest.fixture
def optional_group() -> Scene:
    path = ROOT / "examples" / "optional-group-mandatory-child.json"
    return Scene.model_validate_json(path.read_text())


@pytest.fixture
def orphan_scene() -> Scene:
    return Scene.model_validate_json((ROOT / "examples" / "non-group-parent.json").read_text())


def test_optional_group_with_mandatory_child_is_not_dropped(optional_group: Scene) -> None:
    # The group is optional and under drop pressure, but it holds a mandatory
    # child, so it must be protected and its mandatory descendant kept on canvas.
    result = optimize_scene(
        OptimizeRequest(scene=optional_group, targetWidth=1080, targetHeight=1350, margin=0.04)
    )
    placed = {b.id for b in result.boxes}
    assert "promo-logo" in placed
    # A lower-priority optional sibling absorbs the pressure instead of the group.
    dropped_steps = [s for s in result.explanation if s.code == "optional-removed"]
    assert dropped_steps
    assert "promo" not in str(dropped_steps[0].metrics["droppedIds"])


def test_dropped_optional_group_lists_descendants() -> None:
    # A fully-optional group (no mandatory descendant) that is dropped must name
    # its descendants in the dropped list so nothing vanishes unrecorded.
    scene = Scene.model_validate(
        {
            "schemaVersion": "1.0.0",
            "canvas": {"width": 1000, "height": 1000},
            "elements": [
                _el("head", "headline", 0.5, optional=False, reading=0, extra={"minHeight": 0.5}),
                _grp("banner", 0.5, reading=1),
                _child("banner-a", "banner", "decoration", 0.3, reading=0),
                _child("banner-b", "banner", "decoration", 0.3, reading=1),
            ],
        }
    )
    result = reflow(
        OptimizeRequest(scene=scene, targetWidth=1000, targetHeight=1000, margin=0.04)
    )
    assert "banner" in result.dropped
    assert "banner-a" in result.dropped and "banner-b" in result.dropped
    assert "banner" not in {b.id for b in result.boxes}


def test_non_group_parent_child_is_placed_and_recorded(orphan_scene: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=orphan_scene, targetWidth=1080, targetHeight=1350, margin=0.04)
    )
    assert "panel-label" in {b.id for b in result.boxes}
    steps = [s for s in result.explanation if s.code == "orphaned-child"]
    assert len(steps) == 1
    assert "panel-label" in str(steps[0].metrics["promotedIds"])


def test_malformed_nesting_is_deterministic(
    optional_group: Scene, orphan_scene: Scene
) -> None:
    for scene in (optional_group, orphan_scene):
        req = OptimizeRequest(scene=scene, targetWidth=1080, targetHeight=1350, margin=0.04)
        assert optimize_scene(req) == optimize_scene(req)


def _grp(el_id: str, height: float, *, reading: int) -> dict:
    return {
        "id": el_id,
        "type": "group",
        "semanticRole": "decoration",
        "parentId": None,
        "x": 0.1,
        "y": 0.1,
        "width": 0.3,
        "height": height,
        "rotation": 0,
        "zIndex": reading,
        "visible": True,
        "optional": True,
        "visual": {"opacity": 1, "luminance": 0.5, "colorCoverage": 0.5},
        "constraints": {"minHeight": height},
        "readingOrder": reading,
        "groupAffinities": [],
    }


def _child(el_id: str, parent_id: str, role: str, height: float, *, reading: int) -> dict:
    return {
        "id": el_id,
        "type": "shape",
        "semanticRole": role,
        "parentId": parent_id,
        "x": 0.12,
        "y": 0.12,
        "width": 0.2,
        "height": height,
        "rotation": 0,
        "zIndex": reading,
        "visible": True,
        "optional": True,
        "visual": {"opacity": 1, "luminance": 0.4, "colorCoverage": 0.5},
        "constraints": {},
        "readingOrder": reading,
        "groupAffinities": [],
    }


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
