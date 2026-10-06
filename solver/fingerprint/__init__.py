"""Deterministic approximation of the six LayoutDNA genes."""

from schemas import FingerprintResponse, Scene

from .alignment import alignment_score
from .grouping import grouping_score
from .hierarchy import hierarchy_score
from .mass import mass_score
from .negative_space import negative_space_score
from .reading_path import reading_path_score


def compute_fingerprint(scene: Scene) -> FingerprintResponse:
    """Return explainable proxies, not learned or perceptually validated gene scores."""
    scores = {
        "visualMass": mass_score(scene),
        "hierarchy": hierarchy_score(scene),
        "readingPath": reading_path_score(scene),
        "alignment": alignment_score(scene),
        "negativeSpace": negative_space_score(scene),
        "grouping": grouping_score(scene),
    }
    return FingerprintResponse(
        scores={key: round(value, 4) for key, value in scores.items()},
        notes=[
            "Scores are deterministic geometric proxies, not the final perceptual fingerprint.",
            "Text semantics and visual salience use fixture metadata when native data "
            "is unavailable.",
        ],
    )


__all__ = ["compute_fingerprint"]
