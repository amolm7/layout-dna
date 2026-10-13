"""Canonical matrix of target canvases the harness reflows every scene into.

The set spans the aspect ratios that break naive contain-scaling: a square
feed post, a tall story, a landscape card, and two wide ad banners. Pixel sizes
are the real-world formats these names refer to.
"""

from __future__ import annotations

from typing import NamedTuple


class Target(NamedTuple):
    name: str
    width: float
    height: float


TARGETS: tuple[Target, ...] = (
    Target("square", 1080, 1080),
    Target("story", 1080, 1920),
    Target("landscape", 1200, 628),
    Target("wide", 970, 250),
    Target("leaderboard", 728, 90),
)
