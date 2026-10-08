"""Deterministic, role-aware constrained reflow.

This module replaces uniform contain-scaling with an intentional layout
re-composition: elements are classified by semantic role, flowed along the axis
that best fits the target canvas, and packed so that mandatory constraints
(fixed aspect ratio, minimum size, logo clear space, locked position,
mandatory-on-canvas) are honored. It is still deterministic and geometry-only
-- there is no gradient descent, optimal transport, or learned model here --
but it genuinely rearranges a composition instead of shrinking it in place.

All geometry is expressed in canvas-normalized coordinates in [0, 1]. Inputs are
normalized to the source canvas; outputs are normalized to the target canvas.

Locked elements and collision resolution
----------------------------------------
An element with ``lockedPosition`` is pinned at its source (x, y), clamped into
the usable safe area, and is taken OUT of the flow: it does not advance the flow
cursor, so flowed neighbors are placed naively as if it were absent and may land
on top of it. A post-placement pass (``_resolve_collisions``) then removes
overlaps between non-background boxes. Strategy, all order-stable:

* Boxes are visited in reading order (``_flow_key``). Locked boxes never move.
* A movable box that overlaps (by more than ``_COLLISION_EPS`` on both axes) a
  box that is already settled -- any locked box or any earlier-visited box -- is
  moved exactly once to the first collision-free candidate position, trying in
  fixed order: below, above, right of, left of each settled box (obstacles
  sorted by (y, x, id)). Candidates must stay inside the usable safe area.
* If no candidate fits, the box is left in place (never hidden) and is not
  counted as resolved.

``collisions_resolved`` is the number of boxes actually moved. There is no
randomness anywhere: identical input yields identical output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas import ElementBox, OptimizeRequest, Scene, SceneElement

# Aspect ratio (target width / height) at or above which we flow left-to-right
# instead of top-to-bottom. Banners (e.g. 728x90 -> 8.09) land here.
HORIZONTAL_ASPECT_THRESHOLD = 2.2

# When optional elements must be removed to fit, lower-priority roles go first.
_DROP_PRIORITY: dict[str, int] = {
    "decoration": 0,
    "subhead": 1,
    "body": 2,
    "cta": 3,
    "hero": 4,
    "headline": 5,
    "logo": 6,
    "background": 7,
    "unknown": 2,
}

# Smallest vertical slice (normalized) we will allocate to any flowed element.
_MIN_BAND = 0.015

# Overlap (per axis, normalized) above which two boxes are considered colliding.
_COLLISION_EPS = 1e-6
# Clear space left between a nudged box and the obstacle it was moved away from.
_RESOLVE_GAP = 0.005


@dataclass
class ReflowResult:
    boxes: list[ElementBox]
    dropped: list[str] = field(default_factory=list)
    flow_axis: str = "vertical"
    reorder_count: int = 0
    collisions_resolved: int = 0


def _source_pixel_ratio(element: SceneElement, scene: Scene) -> float:
    """Width/height ratio of an element in source pixels."""
    w = element.width * scene.canvas.width
    h = element.height * scene.canvas.height
    return w / h if h > 1e-9 else 1.0


def _flow_key(element: SceneElement) -> tuple[int, int, str]:
    """Stable ordering: declared readingOrder first, then z-index, then id."""
    order = element.readingOrder if element.readingOrder is not None else 10_000
    return (order, element.zIndex, element.id)


def _is_background(element: SceneElement) -> bool:
    covers_canvas = element.width >= 0.98 and element.height >= 0.98
    return element.semanticRole == "background" or covers_canvas


def reflow(request: OptimizeRequest) -> ReflowResult:
    """Produce target-normalized boxes for a re-composed layout."""
    scene = request.scene
    margin = request.margin
    target_w = request.targetWidth
    target_h = request.targetHeight
    target_aspect = target_w / target_h

    usable_x0, usable_y0 = margin, margin
    usable_w = 1.0 - 2 * margin
    usable_h = 1.0 - 2 * margin

    visible = [e for e in scene.elements if e.visible]
    backgrounds = [e for e in visible if _is_background(e)]
    foreground = [e for e in visible if not _is_background(e)]

    ordered = sorted(foreground, key=_flow_key)
    # How many elements changed neighbor order vs. their raw document order?
    raw_order = sorted(foreground, key=lambda e: (e.zIndex, e.id))
    reorder_count = sum(1 for a, b in zip(ordered, raw_order, strict=True) if a.id != b.id)

    # Drop optional elements only under space pressure, lowest priority first.
    horizontal = target_aspect >= HORIZONTAL_ASPECT_THRESHOLD
    kept, dropped = _apply_drop_policy(ordered, usable_w if horizontal else usable_h)

    boxes: list[ElementBox] = []

    # Backgrounds bleed to the full target canvas, behind everything.
    for bg in backgrounds:
        boxes.append(
            ElementBox(id=bg.id, x=0.0, y=0.0, width=1.0, height=1.0, rotation=bg.rotation)
        )

    args = (kept, scene, target_w, target_h, usable_x0, usable_y0, usable_w, usable_h)
    if horizontal:
        axis = "horizontal"
        placed = _flow_horizontal(*args)
    else:
        axis = "vertical"
        placed = _flow_vertical(*args)

    flow_rank = {e.id: i for i, e in enumerate(kept)}
    locked_ids = {e.id for e in kept if e.constraints.lockedPosition}
    placed, collisions_resolved = _resolve_collisions(
        placed, flow_rank, locked_ids, usable_x0, usable_y0, usable_w, usable_h
    )

    boxes.extend(placed)
    return ReflowResult(
        boxes=boxes,
        dropped=dropped,
        flow_axis=axis,
        reorder_count=reorder_count,
        collisions_resolved=collisions_resolved,
    )


def _overlaps(a: ElementBox, b: ElementBox) -> bool:
    ox = min(a.x + a.width, b.x + b.width) - max(a.x, b.x)
    oy = min(a.y + a.height, b.y + b.height) - max(a.y, b.y)
    return ox > _COLLISION_EPS and oy > _COLLISION_EPS


def _resolve_collisions(
    placed: list[ElementBox],
    flow_rank: dict[str, int],
    locked_ids: set[str],
    x0: float,
    y0: float,
    usable_w: float,
    usable_h: float,
) -> tuple[list[ElementBox], int]:
    """Nudge overlapping non-background boxes apart; see module docstring.

    Returns the boxes (original order preserved) and how many were moved.
    """
    tol = 1e-9
    by_id = {b.id: b for b in placed}
    visit = sorted(by_id, key=lambda i: (flow_rank.get(i, len(flow_rank)), i))
    settled: list[ElementBox] = [by_id[i] for i in visit if i in locked_ids]
    moved = 0

    def fits(box: ElementBox) -> bool:
        return (
            box.x >= x0 - tol
            and box.y >= y0 - tol
            and box.x + box.width <= x0 + usable_w + tol
            and box.y + box.height <= y0 + usable_h + tol
        )

    for box_id in visit:
        if box_id in locked_ids:
            continue
        box = by_id[box_id]
        if any(_overlaps(box, other) for other in settled):
            obstacles = sorted(settled, key=lambda o: (o.y, o.x, o.id))
            candidates: list[tuple[float, float]] = []
            candidates += [(box.x, o.y + o.height + _RESOLVE_GAP) for o in obstacles]  # below
            candidates += [(box.x, o.y - box.height - _RESOLVE_GAP) for o in obstacles]  # above
            candidates += [(o.x + o.width + _RESOLVE_GAP, box.y) for o in obstacles]  # right
            candidates += [(o.x - box.width - _RESOLVE_GAP, box.y) for o in obstacles]  # left
            for cx, cy in candidates:
                trial = box.model_copy(update={"x": cx, "y": cy})
                if fits(trial) and not any(_overlaps(trial, other) for other in settled):
                    box = trial
                    by_id[box_id] = trial
                    moved += 1
                    break
        settled.append(box)

    return [by_id[b.id] for b in placed], moved


def _apply_drop_policy(
    ordered: list[SceneElement], available: float
) -> tuple[list[SceneElement], list[str]]:
    """Remove optional elements, lowest priority first, until min demand fits.

    Mandatory elements (optional is False) are never removed; this keeps the
    AGENTS.md guarantee that mandatory design elements are not silently hidden.
    """
    kept = list(ordered)
    dropped: list[str] = []

    def min_demand(items: list[SceneElement]) -> float:
        return sum(max(e.constraints.minHeight or _MIN_BAND, _MIN_BAND) for e in items)

    optional_sorted = sorted(
        (e for e in ordered if e.optional),
        key=lambda e: (_DROP_PRIORITY.get(e.semanticRole, 2), e.zIndex, e.id),
    )
    idx = 0
    while min_demand(kept) > available and idx < len(optional_sorted):
        victim = optional_sorted[idx]
        kept.remove(victim)
        dropped.append(victim.id)
        idx += 1
    return kept, dropped


def _target_width_for(element: SceneElement, usable_w: float) -> float:
    """Role-driven width within the usable column (left-aligned grid)."""
    role = element.semanticRole
    if role in ("logo", "decoration"):
        # Brand marks and accents keep their footprint; they should not grow to
        # fill the column just because the canvas got wider.
        base = min(usable_w, max(element.constraints.minWidth or 0.0, element.width))
    elif role == "cta":
        base = min(usable_w, max(element.constraints.minWidth or 0.0, usable_w * 0.42))
    elif role in ("body", "subhead"):
        base = usable_w * 0.9
    else:  # headline, hero, unknown
        base = usable_w
    return max(base, element.constraints.minWidth or 0.0)


def _flow_vertical(
    items: list[SceneElement],
    scene: Scene,
    target_w: float,
    target_h: float,
    x0: float,
    y0: float,
    usable_w: float,
    usable_h: float,
) -> list[ElementBox]:
    if not items:
        return []

    widths: dict[str, float] = {}
    heights: dict[str, float] = {}
    for e in items:
        w = min(_target_width_for(e, usable_w), usable_w)
        if e.constraints.fixedAspectRatio:
            ratio = _source_pixel_ratio(e, scene)
            h = (w * target_w / ratio) / target_h
        else:
            # Keep each element's share of vertical space close to the source.
            h = max(e.height, _MIN_BAND)
        widths[e.id] = w
        heights[e.id] = max(h, e.constraints.minHeight or 0.0)

    # Fit heights into the usable column, leaving room for inter-element gaps.
    n = len(items)
    gap_budget = min(0.06, usable_h * 0.25)
    total_h = sum(heights.values())
    room_for_elements = max(usable_h - gap_budget, usable_h * 0.5)
    if total_h > room_for_elements:
        # Shrink non-fixed elements first to protect hero/logo proportions.
        flexible = [e for e in items if not e.constraints.fixedAspectRatio]
        fixed_h = sum(heights[e.id] for e in items if e.constraints.fixedAspectRatio)
        flex_h = sum(heights[e.id] for e in flexible)
        allowance = room_for_elements - fixed_h
        if flexible and flex_h > 0 and allowance > 0:
            scale = allowance / flex_h
            for e in flexible:
                heights[e.id] = max(heights[e.id] * scale, e.constraints.minHeight or _MIN_BAND)
        total_h = sum(heights.values())
        if total_h > usable_h:  # last resort: scale everything
            scale = usable_h / total_h
            for e in items:
                heights[e.id] *= scale
            total_h = usable_h

    gap = (usable_h - sum(heights.values())) / (n + 1) if n else 0.0
    gap = max(gap, 0.0)

    boxes: list[ElementBox] = []
    cursor = y0 + gap
    for e in items:
        w = widths[e.id]
        h = heights[e.id]
        if e.constraints.lockedPosition:
            x = min(max(e.x, x0), x0 + usable_w - w)
            y = min(max(e.y, y0), y0 + usable_h - h)
            boxes.append(ElementBox(id=e.id, x=x, y=y, width=w, height=h, rotation=e.rotation))
            continue  # pinned and out of flow: does not advance the cursor
        elif e.semanticRole == "logo":
            clear = e.constraints.logoClearSpace
            x = x0 + usable_w - w - clear  # anchor brand mark to the right edge
        elif e.semanticRole in ("headline", "body", "subhead", "cta"):
            x = x0  # shared left alignment axis
        else:
            x = x0 + (usable_w - w) / 2  # center feature imagery
        boxes.append(ElementBox(id=e.id, x=x, y=cursor, width=w, height=h, rotation=e.rotation))
        cursor += h + gap
    return boxes


def _flow_horizontal(
    items: list[SceneElement],
    scene: Scene,
    target_w: float,
    target_h: float,
    x0: float,
    y0: float,
    usable_w: float,
    usable_h: float,
) -> list[ElementBox]:
    """Left-to-right flow for wide, short canvases (banners)."""
    if not items:
        return []

    weights = [max(e.width, 0.05) for e in items]
    total_w = sum(weights)
    gap = min(0.03, usable_w * 0.1 / max(len(items), 1))
    content_w = usable_w - gap * (len(items) - 1)

    boxes: list[ElementBox] = []
    cursor = x0
    for e, weight in zip(items, weights, strict=True):
        w = max(content_w * weight / total_w, e.constraints.minWidth or 0.0)
        if e.constraints.fixedAspectRatio:
            ratio = _source_pixel_ratio(e, scene)
            h = (w * target_w / ratio) / target_h
            h = min(h, usable_h)
            # Re-derive width so the ratio survives the height clamp.
            w = (h * target_h) * ratio / target_w
        else:
            h = min(usable_h, max(usable_h * 0.8, e.constraints.minHeight or 0.0))
        y = y0 + (usable_h - h) / 2  # vertically centered band
        if e.constraints.lockedPosition:
            x = min(max(e.x, x0), x0 + usable_w - w)
            boxes.append(ElementBox(id=e.id, x=x, y=y, width=w, height=h, rotation=e.rotation))
            continue  # pinned and out of flow: does not advance the cursor
        boxes.append(ElementBox(id=e.id, x=cursor, y=y, width=w, height=h, rotation=e.rotation))
        cursor += w + gap
    return boxes
