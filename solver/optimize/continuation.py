from schemas import Canvas, ElementBox, ExplanationStep, OptimizeRequest, OptimizeResponse

from .constraints import clamp_to_margin
from .losses import placeholder_drift


def optimize_scene(request: OptimizeRequest) -> OptimizeResponse:
    """Apply a deterministic contain transform; this is not a differentiable solver."""
    scene = request.scene
    source_width = scene.canvas.width
    source_height = scene.canvas.height
    target_width = request.targetWidth
    target_height = request.targetHeight
    usable_width = target_width * (1 - 2 * request.margin)
    usable_height = target_height * (1 - 2 * request.margin)
    scale = min(usable_width / source_width, usable_height / source_height)
    offset_x = (target_width - source_width * scale) / 2
    offset_y = (target_height - source_height * scale) / 2

    boxes: list[ElementBox] = []
    for element in scene.elements:
        box = ElementBox(
            id=element.id,
            x=(offset_x + element.x * source_width * scale) / target_width,
            y=(offset_y + element.y * source_height * scale) / target_height,
            width=element.width * source_width * scale / target_width,
            height=element.height * source_height * scale / target_height,
            rotation=element.rotation,
        )
        clearance = element.constraints.logoClearSpace
        boxes.append(clamp_to_margin(box, max(request.margin, clearance)))

    drift = placeholder_drift(scene, boxes, target_width / target_height)
    return OptimizeResponse(
        target=Canvas(
            width=target_width, height=target_height, backgroundColor=scene.canvas.backgroundColor
        ),
        boxes=boxes,
        geneDrift=drift,
        explanation=[
            ExplanationStep(
                code="contain-scale",
                message="Uniformly scaled the source composition into the target safe area.",
                metrics={"scale": round(scale, 6), "margin": request.margin},
            ),
            ExplanationStep(
                code="margin-clamp",
                message="Clamped element boxes to margins and declared logo clear space.",
                metrics={"elementCount": float(len(boxes))},
            ),
            ExplanationStep(
                code="placeholder-warning",
                message=(
                    "This deterministic transform is a scaffold, not the final "
                    "differentiable optimizer."
                ),
                metrics={"finalSolver": False},
            ),
        ],
    )
