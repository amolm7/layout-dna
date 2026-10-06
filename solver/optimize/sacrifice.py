"""Future explainable gene-sacrifice policy boundary."""

from schemas import GeneName


def ranked_sacrifices(drift: dict[GeneName, float]) -> list[tuple[GeneName, float]]:
    return sorted(drift.items(), key=lambda item: (-item[1], item[0]))
