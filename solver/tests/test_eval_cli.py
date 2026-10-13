"""Tests for the evaluation CLI, feasibility classification, and the CI gate.

These cover TASK-2: the honest pass/fail gate (feasible cases must be clean while
extreme-aspect cases are best-effort), the pure table/gate helpers, and the
``python -m evaluation`` entry point. They live apart from ``test_eval.py`` so the
harness-core tests and the CLI tests stay independently readable.
"""

import json

from evaluation.__main__ import format_table, gate, main, violations_on_feasible
from evaluation.feasibility import ASPECT_STRESS_LIMIT, aspect_stress, feasible_expected
from evaluation.harness import EXAMPLES_DIR, run_evaluation
from evaluation.targets import TARGETS
from schemas import Scene

FEED = {"square", "story", "landscape"}
BANNER = {"wide", "leaderboard"}


def _scene(name: str) -> Scene:
    return Scene.model_validate_json((EXAMPLES_DIR / f"{name}.json").read_text())


def _target(name: str):
    return next(t for t in TARGETS if t.name == name)


# --- feasibility heuristic ---------------------------------------------------


def test_aspect_stress_is_symmetric_and_at_least_one() -> None:
    scene = _scene("editorial-poster")
    for target in TARGETS:
        assert aspect_stress(scene, target) >= 1.0 - 1e-9


def test_square_target_has_near_unit_stress_for_square_scene() -> None:
    # retail-promo is a 1:1 canvas, so the square target is an identity in aspect.
    assert abs(aspect_stress(_scene("retail-promo"), _target("square")) - 1.0) < 1e-9


def test_feed_targets_are_feasible_and_banners_are_not() -> None:
    scene = _scene("editorial-poster")
    for target in TARGETS:
        expected = target.name in FEED
        assert feasible_expected(scene, target) is expected, target.name


def test_threshold_separates_feed_from_banner_for_every_scene() -> None:
    for path in EXAMPLES_DIR.glob("*.json"):
        scene = Scene.model_validate_json(path.read_text())
        for target in TARGETS:
            stress = aspect_stress(scene, target)
            if target.name in FEED:
                assert stress <= ASPECT_STRESS_LIMIT, (path.stem, target.name, stress)
            elif target.name in BANNER:
                assert stress > ASPECT_STRESS_LIMIT, (path.stem, target.name, stress)


# --- gate --------------------------------------------------------------------


def test_feasible_cases_are_violation_free() -> None:
    for case in run_evaluation()["cases"]:
        if case["feasibleExpected"]:
            assert case["violations"]["total"] == 0, (case["scene"], case["target"])


def test_at_least_one_infeasible_case_still_violates() -> None:
    # Non-vacuous: the gate passes because violations are confined to infeasible
    # cases, not because nothing ever violates.
    cases = run_evaluation()["cases"]
    infeasible_violations = [
        c for c in cases if not c["feasibleExpected"] and c["violations"]["total"] > 0
    ]
    assert infeasible_violations, "expected at least one honest infeasible-aspect violation"


def test_gate_passes_on_current_baseline() -> None:
    assert gate(run_evaluation()) == 0


def test_gate_fails_when_a_feasible_case_violates() -> None:
    report = {
        "summary": {"allDeterministic": True},
        "cases": [{"feasibleExpected": True, "violations": {"total": 1}}],
    }
    assert gate(report) == 1
    assert violations_on_feasible(report) == 1


def test_gate_fails_on_non_determinism() -> None:
    report = {
        "summary": {"allDeterministic": False},
        "cases": [{"feasibleExpected": True, "violations": {"total": 0}}],
    }
    assert gate(report) == 1


# --- output ------------------------------------------------------------------


def test_report_is_json_round_trippable() -> None:
    report = run_evaluation()
    assert json.loads(json.dumps(report)) == report


def test_format_table_marks_infeasible_rows_and_shows_disclaimer() -> None:
    table = format_table(run_evaluation())
    assert "best-effort" in table
    assert "proxy" in table.lower()
    assert "scene" in table and "target" in table


def test_main_returns_zero_on_baseline_for_table_and_json(capsys) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out.strip()
    assert main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)  # valid JSON on stdout
