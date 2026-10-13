"""Approximate text-overflow estimation for solved layouts.

This is an honest heuristic, NOT a real text layout engine (AGENTS.md: label
simulations clearly). It estimates whether a text element's content can still
fit its solved box at a readable size after the reflow shrinks or reshapes the
box. It never changes geometry and never drops text; it only reports a shortfall
so the explanation trace can surface it instead of letting text silently clip.

The model is deliberately simple and deterministic:

* A glyph's average advance is about half the font size (``CHAR_WIDTH_RATIO``),
  so ``chars_per_line = box_width_px / (fontSize * CHAR_WIDTH_RATIO)``.
* Wrapping the content gives ``lines``; required height is
  ``lines * fontSize * lineHeight``.
* ``overflowRatio = required_height_px / box_height_px``. Shrinking the font by
  factor ``k`` scales required height by about ``k**2`` (narrower lines *and*
  shorter lines), so the font size that would just fit is
  ``fontSize / sqrt(overflowRatio)`` -- the ``estimatedFontPx``.

A text element is flagged when it cannot fit at its source size
(``overflowRatio`` above a small tolerance) OR when fitting it would require a
font smaller than ``MIN_READABLE_PX``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt

from schemas import Canvas, ElementBox, SceneElement

# Average glyph advance as a fraction of the font size for proportional fonts.
CHAR_WIDTH_RATIO = 0.5
# Smallest font size (target px) we treat as legible body text.
MIN_READABLE_PX = 12.0
# Relative slack so a box that fits its text almost exactly is not flagged.
OVERFLOW_TOL = 0.02
# Fallback line height when the source does not declare one.
_DEFAULT_LINE_HEIGHT = 1.2


@dataclass(frozen=True)
class TextFit:
    element_id: str
    requiredPx: float
    availablePx: float
    overflowRatio: float
    estimatedFontPx: float


def text_overflow(
    element: SceneElement,
    box: ElementBox,
    source_canvas: Canvas,
    target_canvas: Canvas,
) -> TextFit | None:
    """Estimate whether ``element``'s text overflows its solved ``box``.

    Returns a :class:`TextFit` describing the shortfall when the content cannot
    fit at a readable size, or ``None`` when it fits comfortably or the element
    carries no measurable text.
    """
    text = element.text
    if text is None or not text.content.strip():
        return None
    font_px = text.fontSize
    if font_px is None or font_px <= 0:
        return None

    box_w_px = box.width * target_canvas.width
    box_h_px = box.height * target_canvas.height
    if box_w_px <= 0 or box_h_px <= 0:
        return None

    line_height = text.lineHeight or _DEFAULT_LINE_HEIGHT
    chars_per_line = max(1, int(box_w_px / (font_px * CHAR_WIDTH_RATIO)))
    lines = max(1, ceil(len(text.content) / chars_per_line))
    required_px = lines * font_px * line_height

    overflow_ratio = required_px / box_h_px
    estimated_font_px = font_px / sqrt(overflow_ratio) if overflow_ratio > 0 else font_px

    overflows = overflow_ratio > 1 + OVERFLOW_TOL
    illegible = estimated_font_px < MIN_READABLE_PX
    if not (overflows or illegible):
        return None

    return TextFit(
        element_id=element.id,
        requiredPx=round(required_px, 2),
        availablePx=round(box_h_px, 2),
        overflowRatio=round(overflow_ratio, 4),
        estimatedFontPx=round(estimated_font_px, 2),
    )
