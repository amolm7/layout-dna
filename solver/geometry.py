"""Shared axis-aligned box geometry for the solver and its evaluation.

All boxes are in normalized ``[0, 1]`` coordinates. Keeping the overlap test in
one place means the reflow collision resolver and the violation metrics agree on
what "overlap" means, differing only in the epsilon each passes in.
"""

from __future__ import annotations

from schemas import ElementBox

# Default numeric slack so floating-point placement at an exact edge is not
# treated as an overlap. Callers may pass their own epsilon.
DEFAULT_EPS = 1e-6


def overlap_extent(a: ElementBox, b: ElementBox) -> tuple[float, float]:
    """Overlap distance on each axis; positive on an axis means they intersect there."""
    ox = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
    oy = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
    return ox, oy


def boxes_overlap(a: ElementBox, b: ElementBox, eps: float = DEFAULT_EPS) -> bool:
    """True when ``a`` and ``b`` overlap on both axes by more than ``eps``."""
    ox, oy = overlap_extent(a, b)
    return ox > eps and oy > eps
