"""Tests for the approximate text-overflow estimator and its explanation step."""

from optimize import optimize_scene
from optimize.text_fit import MIN_READABLE_PX, TextFit, text_overflow
from schemas import Canvas, ElementBox, OptimizeRequest, Scene, SceneElement, TextProperties

SOURCE = Canvas(width=1080, height=1350)
TARGET = Canvas(width=1080, height=1350)

LONG = "Weekend market opens this Saturday morning downtown by the river at nine"


def _text_element(content: str, font_px: float | None = 64.0) -> SceneElement:
    return SceneElement(
        id="headline",
        type="text",
        semanticRole="headline",
        x=0.08,
        y=0.1,
        width=0.8,
        height=0.12,
        rotation=0,
        zIndex=0,
        visible=True,
        optional=False,
        text=TextProperties(content=content, fontSize=font_px, lineHeight=1.1),
        visual={"opacity": 1, "luminance": 0.1, "colorCoverage": 0.6},
        constraints={"mandatoryOnCanvas": True},
        readingOrder=0,
    )


def _box(width: float, height: float) -> ElementBox:
    return ElementBox(id="headline", x=0.08, y=0.1, width=width, height=height, rotation=0)


def test_comfortable_box_does_not_overflow() -> None:
    fit = text_overflow(_text_element(LONG), _box(0.8, 0.3), SOURCE, TARGET)
    assert fit is None


def test_cramped_box_overflows() -> None:
    fit = text_overflow(_text_element(LONG), _box(0.8, 0.04), SOURCE, TARGET)
    assert isinstance(fit, TextFit)
    assert fit.element_id == "headline"
    assert fit.overflowRatio > 1
    assert fit.requiredPx > fit.availablePx


def test_element_without_text_is_skipped() -> None:
    element = _text_element(LONG)
    no_text = element.model_copy(update={"type": "shape", "text": None})
    assert text_overflow(no_text, _box(0.8, 0.04), SOURCE, TARGET) is None


def test_empty_content_is_skipped() -> None:
    assert text_overflow(_text_element("   "), _box(0.1, 0.01), SOURCE, TARGET) is None


def test_illegible_shrink_is_flagged() -> None:
    # A long headline crushed into a sliver: fitting it would need a font well
    # below the readable floor, so the estimator flags it as illegible.
    fit = text_overflow(_text_element(LONG * 2), _box(0.3, 0.01), SOURCE, TARGET)
    assert isinstance(fit, TextFit)
    assert fit.estimatedFontPx < MIN_READABLE_PX


def _scene(content: str) -> Scene:
    return Scene(schemaVersion="1.0.0", canvas=SOURCE, elements=[_text_element(content)])


def _overflow_steps(scene: Scene, width: float, height: float) -> list:
    response = optimize_scene(
        OptimizeRequest(scene=scene, targetWidth=width, targetHeight=height, margin=0.04)
    )
    return [s for s in response.explanation if s.code == "text-overflow"]


def test_cramped_target_emits_one_overflow_step() -> None:
    steps = _overflow_steps(_scene(LONG), 728, 90)
    assert len(steps) == 1
    assert "headline" in str(steps[0].metrics["overflowingIds"])
    assert steps[0].metrics["worstOverflowRatio"] > 1


def test_comfortable_target_emits_no_overflow_step() -> None:
    assert _overflow_steps(_scene("Hello"), 1080, 1350) == []


def test_overflowing_text_is_still_placed() -> None:
    response = optimize_scene(
        OptimizeRequest(scene=_scene(LONG), targetWidth=728, targetHeight=90, margin=0.04)
    )
    assert "headline" in {b.id for b in response.boxes}


def test_overflow_estimate_is_deterministic() -> None:
    req = OptimizeRequest(scene=_scene(LONG), targetWidth=728, targetHeight=90, margin=0.04)
    assert optimize_scene(req) == optimize_scene(req)
