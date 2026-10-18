"""Unit tests for the six deterministic gene proxies and compute_fingerprint.

These assert documented geometric behaviour only; the scores are proxies, not
perceptual quality measures (see AGENTS.md).
"""

import pytest

from fingerprint import compute_fingerprint
from fingerprint.alignment import alignment_score
from fingerprint.grouping import grouping_score
from fingerprint.hierarchy import hierarchy_score
from fingerprint.mass import mass_score
from fingerprint.negative_space import negative_space_score
from fingerprint.reading_path import reading_path_score
from schemas import Scene, SceneElement

_TOL = 1e-6


def _el(**overrides: object) -> SceneElement:
    base: dict[str, object] = {
        "id": "e",
        "type": "shape",
        "semanticRole": "decoration",
        "x": 0.0,
        "y": 0.0,
        "width": 0.1,
        "height": 0.1,
        "rotation": 0.0,
        "zIndex": 0,
        "visible": True,
        "optional": False,
        "visual": {"opacity": 1.0, "luminance": 0.5, "colorCoverage": 1.0},
    }
    base.update(overrides)
    return SceneElement.model_validate(base)


def _scene(*elements: SceneElement) -> Scene:
    return Scene(
        schemaVersion="1.0.0",
        canvas={"width": 1000, "height": 1000},
        elements=list(elements),
    )


class TestMass:
    def test_empty_scene_scores_zero(self) -> None:
        assert mass_score(_scene()) == 0.0

    def test_full_canvas_fully_opaque_saturates(self) -> None:
        assert mass_score(_scene(_el(id="a", width=1.0, height=1.0))) == pytest.approx(1.0)

    def test_area_opacity_and_coverage_scale_mass(self) -> None:
        half_area = _el(id="a", width=0.5, height=1.0)
        assert mass_score(_scene(half_area)) == pytest.approx(0.5, abs=_TOL)
        half_opacity = _el(
            id="b",
            width=1.0,
            height=1.0,
            visual={"opacity": 0.5, "luminance": 0.5, "colorCoverage": 1.0},
        )
        assert mass_score(_scene(half_opacity)) == pytest.approx(0.5, abs=_TOL)


class TestHierarchy:
    def test_single_element_is_unambiguous(self) -> None:
        assert hierarchy_score(_scene(_el(id="a"))) == 1.0

    def test_empty_scene_scores_zero(self) -> None:
        assert hierarchy_score(_scene()) == 0.0

    def test_equal_areas_give_flat_hierarchy(self) -> None:
        a = _el(id="a", width=0.3, height=0.3)
        b = _el(id="b", width=0.3, height=0.3)
        assert hierarchy_score(_scene(a, b)) == pytest.approx(0.25, abs=_TOL)

    def test_dominant_element_saturates(self) -> None:
        big = _el(id="a", width=0.8, height=1.0)
        small = _el(id="b", width=0.1, height=1.0)
        assert hierarchy_score(_scene(big, small)) == pytest.approx(1.0)


class TestReadingPath:
    def test_no_ordered_elements_scores_zero(self) -> None:
        assert reading_path_score(_scene(_el(id="a"))) == 0.0

    def test_coincident_centers_score_full(self) -> None:
        a = _el(id="a", x=0.0, y=0.0, width=0.2, height=0.2, readingOrder=0)
        b = _el(id="b", x=0.0, y=0.0, width=0.2, height=0.2, readingOrder=1)
        assert reading_path_score(_scene(a, b)) == pytest.approx(1.0, abs=_TOL)

    def test_far_apart_centers_collapse_to_zero(self) -> None:
        a = _el(id="a", x=0.0, y=0.0, width=0.0, height=0.0, readingOrder=0)
        b = _el(id="b", x=1.0, y=1.0, width=0.0, height=0.0, readingOrder=1)
        assert reading_path_score(_scene(a, b)) == 0.0


class TestAlignment:
    def test_single_element_is_aligned(self) -> None:
        assert alignment_score(_scene(_el(id="a"))) == 1.0

    def test_shared_edge_counts_as_aligned(self) -> None:
        a = _el(id="a", x=0.1, width=0.2)
        b = _el(id="b", x=0.1, width=0.4)
        assert alignment_score(_scene(a, b)) == pytest.approx(1.0)

    def test_disjoint_axes_score_zero(self) -> None:
        a = _el(id="a", x=0.0, width=0.1)
        b = _el(id="b", x=0.5, width=0.1)
        assert alignment_score(_scene(a, b)) == 0.0


class TestNegativeSpace:
    def test_empty_canvas_is_all_space(self) -> None:
        assert negative_space_score(_scene()) == 1.0

    def test_full_coverage_leaves_no_space(self) -> None:
        assert negative_space_score(_scene(_el(id="a", width=1.0, height=1.0))) == 0.0

    def test_ignores_invisible_elements(self) -> None:
        visible = _el(id="a", width=0.5, height=1.0)
        hidden = _el(id="b", width=0.5, height=1.0, visible=False)
        assert negative_space_score(_scene(visible, hidden)) == pytest.approx(0.5, abs=_TOL)


class TestGrouping:
    def test_ungrouped_elements_score_zero(self) -> None:
        assert grouping_score(_scene(_el(id="a"), _el(id="b"))) == 0.0

    def test_group_affinities_and_parents_count_as_grouped(self) -> None:
        grouped = _el(id="a", groupAffinities=["brand"])
        parented = _el(id="b", parentId="a")
        assert grouping_score(_scene(grouped, parented)) == pytest.approx(1.0)

    def test_partial_grouping(self) -> None:
        grouped = _el(id="a", groupAffinities=["brand"])
        loose = _el(id="b")
        assert grouping_score(_scene(grouped, loose)) == pytest.approx(0.5, abs=_TOL)


class TestComputeFingerprint:
    def test_reports_all_six_genes_in_unit_range(self) -> None:
        scene = _scene(
            _el(id="a", semanticRole="headline", width=0.6, height=0.2, readingOrder=0),
            _el(id="b", semanticRole="logo", x=0.6, y=0.8, width=0.2, height=0.1, readingOrder=1),
        )
        result = compute_fingerprint(scene)
        assert set(result.scores) == {
            "visualMass",
            "hierarchy",
            "readingPath",
            "alignment",
            "negativeSpace",
            "grouping",
        }
        for value in result.scores.values():
            assert 0.0 <= value <= 1.0

    def test_scores_are_rounded_and_deterministic(self) -> None:
        scene = _scene(
            _el(
                id="a",
                width=0.33333,
                height=0.7,
                visual={"opacity": 0.9, "luminance": 0.5, "colorCoverage": 0.8},
            )
        )
        first = compute_fingerprint(scene)
        assert compute_fingerprint(scene).scores == first.scores
        for value in first.scores.values():
            assert round(value, 4) == value

    def test_notes_flag_the_proxy_nature(self) -> None:
        result = compute_fingerprint(_scene(_el(id="a")))
        assert any("prox" in note.lower() for note in result.notes)
