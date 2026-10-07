from schemas import ElementBox


def clamp_to_margin(box: ElementBox, margin: float) -> ElementBox:
    width = min(box.width, 1 - 2 * margin)
    height = min(box.height, 1 - 2 * margin)
    # Guard the upper bounds: when an element fills the safe area exactly,
    # 1 - margin - size can underflow just below `margin` in float math and
    # pull the box back outside the margin, so never let it drop below `margin`.
    max_x = max(margin, 1 - margin - width)
    max_y = max(margin, 1 - margin - height)
    return box.model_copy(
        update={
            "x": min(max(box.x, margin), max_x),
            "y": min(max(box.y, margin), max_y),
            "width": width,
            "height": height,
        }
    )
