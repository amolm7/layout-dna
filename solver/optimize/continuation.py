from schemas import Canvas, ElementBox, ExplanationStep, OptimizeRequest, OptimizeResponse

from .constraints import clamp_to_margin
from .losses import measure_drift
from .reflow import reflow
from .sacrifice import ranked_sacrifices


def optimize_scene(request: OptimizeRequest) -> OptimizeResponse:
    """Re-compose the source layout for the target canvas.

    Deterministic and geometry-only: a role-aware constrained reflow, not a
    differentiable optimizer. Gradient- and optimal-transport-based refinement
    remain future work behind this same HTTP contract.
    """
    scene = request.scene
    result = reflow(request)

    background_ids = {box.id for box in result.boxes if box.width >= 0.999 and box.height >= 0.999}
    fixed_aspect_ids = {e.id for e in scene.elements if e.constraints.fixedAspectRatio}

    boxes: list[ElementBox] = []
    for box in result.boxes:
        if box.id in background_ids:
            boxes.append(box)  # full-bleed backgrounds are intentionally outside the safe area
        else:
            boxes.append(clamp_to_margin(box, request.margin))

    target = Canvas(
        width=request.targetWidth,
        height=request.targetHeight,
        backgroundColor=scene.canvas.backgroundColor,
    )
    drift = measure_drift(scene, boxes, target)
    ranked = ranked_sacrifices(drift)
    top_gene, top_value = ranked[0] if ranked else ("visualMass", 0.0)

    fixed_placed = sum(1 for box in boxes if box.id in fixed_aspect_ids)

    explanation = [
        ExplanationStep(
            code="reflow",
            message=(
                f"Re-composed the layout along the {result.flow_axis} axis, "
                f"placing {len(boxes)} element(s) in reading order."
            ),
            metrics={
                "axis": result.flow_axis,
                "elementsPlaced": float(len(boxes)),
                "reorderedElements": float(result.reorder_count),
            },
        ),
        ExplanationStep(
            code="constraints",
            message=(
                "Honored fixed aspect ratios, minimum sizes, logo clear space, and "
                "the target safe margin."
            ),
            metrics={
                "fixedAspectHonored": float(fixed_placed),
                "margin": request.margin,
            },
        ),
    ]

    if result.dropped:
        explanation.append(
            ExplanationStep(
                code="optional-removed",
                message=(
                    "Removed optional element(s) that did not fit the target safe area: "
                    + ", ".join(result.dropped)
                    + "."
                ),
                metrics={
                    "droppedIds": ", ".join(result.dropped),
                    "droppedCount": float(len(result.dropped)),
                },
            )
        )

    if result.collisions_resolved:
        explanation.append(
            ExplanationStep(
                code="collisions-resolved",
                message=(
                    f"Nudged {result.collisions_resolved} element(s) to remove overlaps "
                    "with locked or earlier-in-reading-order elements."
                ),
                metrics={"collisionsResolved": float(result.collisions_resolved)},
            )
        )

    explanation.append(
        ExplanationStep(
            code="gene-drift",
            message=(
                f"Measured structural drift against the source fingerprint; "
                f"'{top_gene}' changed most ({top_value})."
            ),
            metrics={"maxDriftGene": top_gene, "maxDrift": top_value},
        )
    )
    explanation.append(
        ExplanationStep(
            code="solver-scope",
            message=(
                "Deterministic role-aware reflow. Differentiable (gradient / "
                "optimal-transport) refinement is not yet implemented."
            ),
            metrics={"finalSolver": False},
        )
    )

    return OptimizeResponse(
        target=target,
        boxes=boxes,
        geneDrift=drift,
        explanation=explanation,
    )
