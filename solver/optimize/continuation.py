from schemas import Canvas, ElementBox, ExplanationStep, OptimizeRequest, OptimizeResponse

from .constraints import clamp_to_margin
from .losses import measure_drift
from .reflow import detect_unmet, reflow
from .sacrifice import ranked_sacrifices
from .text_fit import text_overflow


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

    if result.promoted:
        explanation.append(
            ExplanationStep(
                code="orphaned-child",
                message=(
                    "Placed "
                    + ", ".join(result.promoted)
                    + " at the top level because their parent is not a group; a non-group "
                    "parent cannot carry children, so they are placed independently rather "
                    "than dropped."
                ),
                metrics={
                    "promotedIds": ", ".join(result.promoted),
                    "promotedCount": float(len(result.promoted)),
                },
            )
        )

    elements_by_id = {element.id: element for element in scene.elements}
    fits = [
        fit
        for box in boxes
        if (element := elements_by_id.get(box.id)) is not None and element.text is not None
        if (fit := text_overflow(element, box, scene.canvas, target)) is not None
    ]
    if fits:
        worst = max(fits, key=lambda f: f.overflowRatio)
        explanation.append(
            ExplanationStep(
                code="text-overflow",
                message=(
                    f"Estimated that {len(fits)} text element(s) may not fit their solved "
                    "box at a readable size: "
                    + ", ".join(f.element_id for f in fits)
                    + ". Approximate heuristic, not a true text layout engine; the text is "
                    "kept, not removed."
                ),
                metrics={
                    "overflowingIds": ", ".join(f.element_id for f in fits),
                    "overflowingCount": float(len(fits)),
                    "worstOverflowRatio": worst.overflowRatio,
                    "minEstimatedFontPx": min(f.estimatedFontPx for f in fits),
                },
            )
        )

    unmet = detect_unmet(boxes, elements_by_id)
    if unmet:
        unmet_ids = sorted({u.id for u in unmet})
        worst = max(unmet, key=lambda u: u.got if u.kind == "overlap" else u.wanted - u.got)
        explanation.append(
            ExplanationStep(
                code="constraint-infeasible",
                message=(
                    "Could not fully honor hard constraints on this target for "
                    + ", ".join(unmet_ids)
                    + ". The element(s) are kept and the shortfall is recorded rather than "
                    "hidden; the layout is best-effort for this canvas."
                ),
                metrics={
                    "unmetIds": ", ".join(unmet_ids),
                    "unmetCount": float(len(unmet)),
                    "kinds": ", ".join(sorted({u.kind for u in unmet})),
                    "worstId": worst.id,
                    "worstKind": worst.kind,
                    "wanted": worst.wanted,
                    "got": worst.got,
                },
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
