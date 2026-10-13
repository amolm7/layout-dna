"""Tests for the self-contained evaluation harness."""

from evaluation.harness import EXAMPLES_DIR, percentile, run_evaluation, runtime_summary
from evaluation.targets import TARGETS

GENES = {
    "visualMass",
    "hierarchy",
    "readingPath",
    "alignment",
    "negativeSpace",
    "grouping",
}
VIOLATION_KEYS = {"margin", "overlap", "minSize", "mandatoryMissing", "logoClearSpace"}
# Targets whose aspect ratio is close enough to the example posters that the
# solver places every element cleanly. The two ad-banner targets (wide,
# leaderboard) are intentionally extreme and surface honest violations that the
# planner is triaging -- see the QUESTION in layout-dna-coord.md.
FEED_TARGETS = {"square", "story", "landscape"}


def test_report_structure() -> None:
    report = run_evaluation()
    assert report["solverKind"] == "deterministic-reflow"
    assert "proxy" in report["disclaimer"].lower()
    assert report["cases"], "expected at least one case"
    assert set(report["summary"]) == {
        "cases",
        "totalViolations",
        "meanAggregateDrift",
        "maxAggregateDrift",
        "allDeterministic",
        "runtime",
    }


def test_covers_every_scene_times_target() -> None:
    report = run_evaluation()
    scenes = {c["scene"] for c in report["cases"]}
    targets = {c["target"] for c in report["cases"]}
    example_count = len(list(EXAMPLES_DIR.glob("*.json")))
    assert len(scenes) == example_count
    assert targets == {t.name for t in TARGETS}
    assert report["summary"]["cases"] == len(scenes) * len(TARGETS)
    assert len(report["cases"]) == report["summary"]["cases"]


def test_every_case_is_deterministic() -> None:
    report = run_evaluation()
    assert report["summary"]["allDeterministic"] is True
    assert all(c["deterministic"] is True for c in report["cases"])


def test_case_fields_are_well_formed() -> None:
    report = run_evaluation()
    for case in report["cases"]:
        assert set(case["geneDrift"]) == GENES
        assert all(0.0 <= v <= 1.0 for v in case["geneDrift"].values())
        assert 0.0 <= case["aggregateDrift"] <= 1.0
        assert case["runtimeMs"] >= 0.0
        assert set(case["violations"]) == VIOLATION_KEYS | {"total"}
        assert case["violations"]["total"] == sum(
            case["violations"][k] for k in VIOLATION_KEYS
        )
        assert isinstance(case["dropped"], list)
        assert case["collisionsResolved"] >= 0


def test_feed_shaped_targets_have_no_violations() -> None:
    report = run_evaluation()
    for case in report["cases"]:
        if case["target"] in FEED_TARGETS:
            assert case["violations"]["total"] == 0, (
                f"{case['scene']} -> {case['target']} regressed: {case['violations']}"
            )


def test_detector_fires_on_infeasible_banner() -> None:
    # The harness must not report everything clean: a fixed-aspect hero cannot
    # fit a 728x90 leaderboard, so the detector should flag a real minSize miss.
    report = run_evaluation()
    leaderboard = [c for c in report["cases"] if c["target"] == "leaderboard"]
    assert any(c["violations"]["total"] > 0 for c in leaderboard)


def test_summary_aggregates_cases() -> None:
    report = run_evaluation()
    cases = report["cases"]
    summary = report["summary"]
    assert summary["totalViolations"] == sum(c["violations"]["total"] for c in cases)
    assert summary["maxAggregateDrift"] == max(c["aggregateDrift"] for c in cases)


def test_percentile_nearest_rank() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    assert percentile(values, 0) == 1.0
    assert percentile(values, 50) == 2.0
    assert percentile(values, 100) == 4.0
    assert percentile([], 95) == 0.0
    # Order independence: shuffled input yields the same percentile.
    assert percentile([4.0, 1.0, 3.0, 2.0], 95) == 4.0


def test_runtime_summary_bounds_and_keys() -> None:
    summary = runtime_summary([5.0, 1.0, 3.0, 2.0, 4.0])
    assert set(summary) == {"minMs", "meanMs", "p50Ms", "p95Ms", "maxMs"}
    assert summary["minMs"] == 1.0
    assert summary["maxMs"] == 5.0
    assert summary["minMs"] <= summary["meanMs"] <= summary["maxMs"]
    assert summary["p50Ms"] <= summary["p95Ms"] <= summary["maxMs"]
    assert runtime_summary([])["meanMs"] == 0.0


def test_report_runtime_summary_is_wired() -> None:
    runtime = run_evaluation()["summary"]["runtime"]
    assert set(runtime) == {"minMs", "meanMs", "p50Ms", "p95Ms", "maxMs"}
    assert runtime["maxMs"] >= runtime["minMs"] >= 0.0
