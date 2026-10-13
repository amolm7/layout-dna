"""Tests for the shared axis-aligned box geometry helper."""

from geometry import DEFAULT_EPS, boxes_overlap, overlap_extent
from schemas import ElementBox


def _box(x: float, y: float, w: float, h: float) -> ElementBox:
    return ElementBox(id="b", x=x, y=y, width=w, height=h, rotation=0.0)


def test_overlap_extent_is_positive_when_boxes_intersect() -> None:
    ox, oy = overlap_extent(_box(0, 0, 0.5, 0.5), _box(0.25, 0.25, 0.5, 0.5))
    assert ox == 0.25
    assert oy == 0.25
    assert boxes_overlap(_box(0, 0, 0.5, 0.5), _box(0.25, 0.25, 0.5, 0.5))


def test_touching_edges_do_not_overlap() -> None:
    # Boxes sharing only an edge have zero extent, which is not > eps.
    assert not boxes_overlap(_box(0, 0, 0.5, 1.0), _box(0.5, 0, 0.5, 1.0))


def test_separated_on_one_axis_is_not_overlap() -> None:
    # Overlap on y but a clear gap on x must not count as an overlap.
    assert not boxes_overlap(_box(0, 0, 0.2, 1.0), _box(0.5, 0, 0.2, 1.0))


def test_eps_controls_sensitivity() -> None:
    a = _box(0, 0, 0.5, 0.5)
    b = _box(0.5 - 2e-6, 0, 0.5, 0.5)  # 2e-6 of overlap on x
    assert boxes_overlap(a, b, DEFAULT_EPS)  # 2e-6 > 1e-6
    assert not boxes_overlap(a, b, 1e-5)  # 2e-6 < 1e-5
