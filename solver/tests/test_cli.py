"""Tests for the standalone ``layoutdna`` command-line interface.

These cover the pure formatters, target resolution (preset vs explicit size),
and the ``main`` entry point end to end over a real example scene, in both the
human-readable and ``--json`` output modes.
"""

import json

import pytest

from cli import (
    TARGET_PRESETS,
    build_parser,
    format_fingerprint,
    format_optimize,
    load_scene,
    main,
)
from evaluation.harness import EXAMPLES_DIR
from fingerprint import compute_fingerprint
from optimize import optimize_scene
from schemas import OptimizeRequest

SCENE_PATH = EXAMPLES_DIR / "retail-promo.json"


def test_load_scene_validates_example() -> None:
    scene = load_scene(SCENE_PATH)
    assert scene.schemaVersion == "1.0.0"
    assert scene.elements


def test_format_fingerprint_lists_every_gene() -> None:
    text = format_fingerprint(compute_fingerprint(load_scene(SCENE_PATH)))
    for gene in ("visualMass", "hierarchy", "readingPath", "alignment",
                 "negativeSpace", "grouping"):
        assert gene in text
    assert "proxy" in text.lower()


def test_format_optimize_shows_boxes_and_trace() -> None:
    request = OptimizeRequest(scene=load_scene(SCENE_PATH), targetWidth=728, targetHeight=90)
    response = optimize_scene(request)
    text = format_optimize(response)
    assert "explanation trace" in text
    for box in response.boxes:
        assert box.id in text


def test_optimize_requires_a_target(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["optimize", str(SCENE_PATH)])


def test_optimize_preset_matches_explicit_size(capsys: pytest.CaptureFixture[str]) -> None:
    width, height = TARGET_PRESETS["leaderboard"]
    assert main(["optimize", str(SCENE_PATH), "--target", "leaderboard", "--json"]) == 0
    from_preset = json.loads(capsys.readouterr().out)
    assert main(
        ["optimize", str(SCENE_PATH), "--width", str(width), "--height", str(height), "--json"]
    ) == 0
    from_explicit = json.loads(capsys.readouterr().out)
    assert from_preset == from_explicit


def test_fingerprint_json_mode_is_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fingerprint", str(SCENE_PATH), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["approximation"] is True
    assert set(payload["scores"]) == {
        "visualMass", "hierarchy", "readingPath", "alignment", "negativeSpace", "grouping"
    }


def test_human_readable_fingerprint_runs(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fingerprint", str(SCENE_PATH)]) == 0
    assert "fingerprint" in capsys.readouterr().out.lower()


def test_parser_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
