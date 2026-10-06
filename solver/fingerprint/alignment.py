from schemas import Scene


def alignment_score(scene: Scene) -> float:
    visible = [element for element in scene.elements if element.visible]
    if len(visible) < 2:
        return 1.0 if visible else 0.0
    aligned_pairs = 0
    pairs = 0
    for index, first in enumerate(visible):
        for second in visible[index + 1 :]:
            pairs += 1
            first_axes = (first.x, first.x + first.width / 2, first.x + first.width)
            second_axes = (second.x, second.x + second.width / 2, second.x + second.width)
            if min(abs(a - b) for a in first_axes for b in second_axes) <= 0.025:
                aligned_pairs += 1
    return aligned_pairs / pairs if pairs else 0.0
