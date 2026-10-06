from schemas import Scene


def grouping_score(scene: Scene) -> float:
    visible = [element for element in scene.elements if element.visible]
    if not visible:
        return 0.0
    assigned = sum(bool(element.parentId or element.groupAffinities) for element in visible)
    return assigned / len(visible)
