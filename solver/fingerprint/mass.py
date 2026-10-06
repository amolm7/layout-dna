from schemas import Scene


def mass_score(scene: Scene) -> float:
    visible = [element for element in scene.elements if element.visible]
    if not visible:
        return 0.0
    # Approximation: occupied area weighted by opacity and declared color coverage.
    mass = sum(
        element.width * element.height * element.visual.opacity * element.visual.colorCoverage
        for element in visible
    )
    return min(1.0, mass)
