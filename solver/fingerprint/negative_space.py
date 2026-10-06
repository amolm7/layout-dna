from schemas import Scene


def negative_space_score(scene: Scene) -> float:
    occupied = sum(element.width * element.height for element in scene.elements if element.visible)
    # Approximation ignores overlap; it is intentionally bounded and deterministic.
    return max(0.0, 1.0 - min(1.0, occupied))
