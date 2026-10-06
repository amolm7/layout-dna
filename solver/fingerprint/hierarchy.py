from schemas import Scene


def hierarchy_score(scene: Scene) -> float:
    visible = [element for element in scene.elements if element.visible]
    if len(visible) < 2:
        return 1.0 if visible else 0.0
    areas = sorted((element.width * element.height for element in visible), reverse=True)
    return min(1.0, (areas[0] / max(areas[1], 1e-9)) / 4)
