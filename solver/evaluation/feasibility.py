"""Aspect-stress classification: can a target plausibly hold a scene's layout?

A hard-constraint violation on a target whose aspect ratio is wildly different
from the source is expected, not a solver defect: a 4:5 poster with a mandatory
fixed-aspect hero cannot inhabit an 8:1 ad banner without breaking a min-size or
overlapping. ``feasible_expected`` separates those extreme cases from the
feed/card formats, where the solver is held to zero violations. This is a
transparent geometric heuristic, NOT a claim that a feasible result looks good.
"""

from __future__ import annotations

from schemas import Scene

from .targets import Target

# Aspect stress is the larger of (target_aspect / source_aspect) and its inverse,
# so it is >= 1 and symmetric; 1.0 means identical aspect ratios. The limit sits
# between the feed/card formats (stress <= ~2.55 against the example scenes) and
# the ad banners (stress >= ~3.88), so a "feasible" case is one the solver has no
# geometric excuse to violate.
ASPECT_STRESS_LIMIT = 3.0


def aspect_stress(scene: Scene, target: Target) -> float:
    """How far ``target``'s aspect ratio is stretched from ``scene``'s (>= 1.0)."""
    source_aspect = scene.canvas.width / scene.canvas.height
    target_aspect = target.width / target.height
    ratio = target_aspect / source_aspect
    return max(ratio, 1.0 / ratio)


def feasible_expected(scene: Scene, target: Target) -> bool:
    """True when the target is close enough in aspect that a clean solve is expected."""
    return aspect_stress(scene, target) <= ASPECT_STRESS_LIMIT
