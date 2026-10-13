"""Hard-constraint violation checks for a single solver result.

Each check returns an integer count so a clean run sums to zero. All geometry is
in target-canvas-normalized coordinates in [0, 1], matching the solver output.
A box is "full bleed" when it covers the whole canvas (backgrounds); such boxes
intentionally sit outside the safe margin and are excluded from the margin and
overlap checks.
"""

from __future__ import annotations

from schemas import ElementBox, OptimizeRequest, OptimizeResponse, Scene

# Numeric slack so floating-point placement at the exact bound is not flagged.
_TOL = 1e-6
# A box this large on both axes is a full-bleed background (see continuation.py).
_FULL_BLEED = 0.999


def _is_full_bleed(box: ElementBox) -> bool:
    return box.width >= _FULL_BLEED and box.height >= _FULL_BLEED


def _overlaps(a: ElementBox, b: ElementBox) -> bool:
    ox = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
    oy = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
    return ox > _TOL and oy > _TOL


def count_violations(
    scene: Scene, request: OptimizeRequest, response: OptimizeResponse
) -> dict[str, int]:
    """Count hard-constraint violations in ``response`` for ``scene``/``request``.

    Returns a dict with one integer per check plus ``total`` (their sum):

    * ``margin`` -- non-full-bleed boxes escaping the safe area ``[m, 1 - m]``.
    * ``overlap`` -- foreground box pairs overlapping on both axes.
    * ``minSize`` -- boxes below their source ``minWidth`` / ``minHeight``.
    * ``mandatoryMissing`` -- ``mandatoryOnCanvas`` elements absent from boxes.
    * ``logoClearSpace`` -- logo boxes closer to a canvas edge than required.
    """
    margin = request.margin
    elements = {e.id: e for e in scene.elements}
    foreground = [b for b in response.boxes if not _is_full_bleed(b)]

    margin_hits = 0
    for box in foreground:
        if (
            box.x < margin - _TOL
            or box.y < margin - _TOL
            or box.x + box.width > 1 - margin + _TOL
            or box.y + box.height > 1 - margin + _TOL
        ):
            margin_hits += 1

    overlap_hits = 0
    for i, first in enumerate(foreground):
        for second in foreground[i + 1 :]:
            if _overlaps(first, second):
                overlap_hits += 1

    min_size_hits = 0
    for box in response.boxes:
        element = elements.get(box.id)
        if element is None:
            continue
        min_w = element.constraints.minWidth
        min_h = element.constraints.minHeight
        if (min_w is not None and box.width < min_w - _TOL) or (
            min_h is not None and box.height < min_h - _TOL
        ):
            min_size_hits += 1

    placed_ids = {b.id for b in response.boxes}
    mandatory_missing = sum(
        1
        for e in scene.elements
        if e.constraints.mandatoryOnCanvas and e.id not in placed_ids
    )

    logo_clear_hits = 0
    for box in response.boxes:
        element = elements.get(box.id)
        if element is None or element.semanticRole != "logo":
            continue
        clear = element.constraints.logoClearSpace
        if clear <= 0:
            continue
        edge_distance = min(
            box.x, box.y, 1 - (box.x + box.width), 1 - (box.y + box.height)
        )
        if edge_distance < clear - _TOL:
            logo_clear_hits += 1

    counts = {
        "margin": margin_hits,
        "overlap": overlap_hits,
        "minSize": min_size_hits,
        "mandatoryMissing": mandatory_missing,
        "logoClearSpace": logo_clear_hits,
    }
    counts["total"] = sum(counts.values())
    return counts
