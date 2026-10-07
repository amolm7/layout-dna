"""Drift measurement for the deterministic reflow solver.

Drift is the absolute change in each of the six gene proxies between the source
composition and the solved target composition. Scores come from the same
deterministic fingerprint modules used by the /fingerprint endpoint, so the
numbers reported in the explanation trace are grounded in an actual measurement
rather than hand-tuned constants.
"""

from __future__ import annotations

from fingerprint.alignment import alignment_score
from fingerprint.grouping import grouping_score
from fingerprint.hierarchy import hierarchy_score
from fingerprint.mass import mass_score
from fingerprint.negative_space import negative_space_score
from fingerprint.reading_path import reading_path_score
from schemas import Canvas, ElementBox, GeneName, Scene, SceneElement

_GENES = {
    "visualMass": mass_score,
    "hierarchy": hierarchy_score,
    "readingPath": reading_path_score,
    "alignment": alignment_score,
    "negativeSpace": negative_space_score,
    "grouping": grouping_score,
}


def build_result_scene(
    scene: Scene, boxes: list[ElementBox], target: Canvas
) -> Scene:
    """Reconstruct a Scene from solved boxes, preserving non-geometry metadata.

    Elements absent from ``boxes`` (dropped optionals) are excluded, so drift
    reflects the composition that is actually rendered.
    """
    by_id = {box.id: box for box in boxes}
    elements: list[SceneElement] = []
    for element in scene.elements:
        box = by_id.get(element.id)
        if box is None:
            continue
        elements.append(
            element.model_copy(
                update={
                    "x": box.x,
                    "y": box.y,
                    "width": box.width,
                    "height": box.height,
                    "rotation": box.rotation,
                    "parentId": element.parentId if element.parentId in by_id else None,
                }
            )
        )
    return Scene(schemaVersion="1.0.0", canvas=target, elements=elements)


def measure_gene_scores(scene: Scene) -> dict[GeneName, float]:
    return {name: fn(scene) for name, fn in _GENES.items()}  # type: ignore[misc]


def measure_drift(
    scene: Scene, boxes: list[ElementBox], target: Canvas
) -> dict[GeneName, float]:
    """Absolute per-gene change between source and solved composition, in [0, 1]."""
    source_scores = measure_gene_scores(scene)
    result_scene = build_result_scene(scene, boxes, target)
    result_scores = measure_gene_scores(result_scene)
    return {
        name: round(min(1.0, abs(source_scores[name] - result_scores[name])), 4)
        for name in source_scores
    }
