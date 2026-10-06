from schemas import ElementBox


def clamp_to_margin(box: ElementBox, margin: float) -> ElementBox:
    width = min(box.width, 1 - 2 * margin)
    height = min(box.height, 1 - 2 * margin)
    return box.model_copy(
        update={
            "x": min(max(box.x, margin), 1 - margin - width),
            "y": min(max(box.y, margin), 1 - margin - height),
            "width": width,
            "height": height,
        }
    )
