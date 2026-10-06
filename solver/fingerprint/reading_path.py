from schemas import Scene


def reading_path_score(scene: Scene) -> float:
    ordered = sorted(
        (
            element
            for element in scene.elements
            if element.visible and element.readingOrder is not None
        ),
        key=lambda element: element.readingOrder or 0,
    )
    if len(ordered) < 2:
        return 1.0 if ordered else 0.0
    distances = [
        abs(a.x + a.width / 2 - (b.x + b.width / 2))
        + abs(a.y + a.height / 2 - (b.y + b.height / 2))
        for a, b in zip(ordered, ordered[1:], strict=False)
    ]
    return max(0.0, 1.0 - sum(distances) / len(distances))
