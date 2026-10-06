from schemas import ElementBox, GeneName, Scene


def placeholder_drift(
    scene: Scene, boxes: list[ElementBox], target_aspect: float
) -> dict[GeneName, float]:
    source_aspect = scene.canvas.width / scene.canvas.height
    aspect_delta = min(1.0, abs(target_aspect - source_aspect) / max(source_aspect, 1e-9))
    clamped = sum(
        abs(box.x - element.x) + abs(box.y - element.y)
        for box, element in zip(boxes, scene.elements, strict=True)
    ) / max(len(boxes), 1)
    movement = min(1.0, clamped)
    return {
        "visualMass": round(aspect_delta * 0.18, 4),
        "hierarchy": 0.0,
        "readingPath": round(movement * 0.25, 4),
        "alignment": round(movement * 0.15, 4),
        "negativeSpace": round(aspect_delta * 0.45, 4),
        "grouping": round(movement * 0.1, 4),
    }
