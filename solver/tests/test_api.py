import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import app
from fingerprint import compute_fingerprint
from optimize import optimize_scene
from schemas import OptimizeRequest, Scene

ROOT = Path(__file__).parents[2]


@pytest.fixture
def scene() -> Scene:
    return Scene.model_validate_json((ROOT / "examples" / "editorial-poster.json").read_text())


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scene_validation_rejects_unknown_parent() -> None:
    payload = json.loads((ROOT / "examples" / "event-flyer.json").read_text())
    payload["elements"][0]["parentId"] = "missing"
    with pytest.raises(ValidationError, match="unknown parentId"):
        Scene.model_validate(payload)


def test_fingerprint_is_deterministic(scene: Scene) -> None:
    first = compute_fingerprint(scene)
    second = compute_fingerprint(scene)
    assert first == second
    assert set(first.scores) == {
        "visualMass",
        "hierarchy",
        "readingPath",
        "alignment",
        "negativeSpace",
        "grouping",
    }
    assert first.approximation is True


def test_target_scaling_preserves_fixed_aspect_ratio(scene: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=scene, targetWidth=1080, targetHeight=1920, margin=0.04)
    )
    source = next(element for element in scene.elements if element.id == "hero")
    target = next(box for box in result.boxes if box.id == "hero")
    source_ratio = source.width * scene.canvas.width / (source.height * scene.canvas.height)
    target_ratio = target.width * result.target.width / (target.height * result.target.height)
    assert target_ratio == pytest.approx(source_ratio)


def test_margin_enforcement(scene: Scene) -> None:
    result = optimize_scene(
        OptimizeRequest(scene=scene, targetWidth=728, targetHeight=90, margin=0.05)
    )
    for box in result.boxes:
        assert box.x >= 0.05
        assert box.y >= 0.05
        assert box.x + box.width <= 0.95 + 1e-9
        assert box.y + box.height <= 0.95 + 1e-9


def test_optimize_endpoint_matches_response_contract(scene: Scene) -> None:
    response = TestClient(app).post(
        "/api/v1/optimize",
        json={"scene": scene.model_dump(), "targetWidth": 1200, "targetHeight": 628},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["solverKind"] == "deterministic-placeholder"
    assert len(body["boxes"]) == len(scene.elements)
    assert body["explanation"][-1]["metrics"]["finalSolver"] is False
