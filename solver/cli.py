"""Standalone command-line interface for the LayoutDNA solver.

Runs the fingerprint and reflow engine on a scene JSON file straight from the
terminal, with no web server and no front-end. This is the self-contained entry
point for the engine:

    layoutdna fingerprint examples/retail-promo.json
    layoutdna optimize   examples/retail-promo.json --target leaderboard
    layoutdna optimize   examples/retail-promo.json --width 970 --height 250 --json

``--json`` emits the raw API response (the exact shape the HTTP endpoints return);
without it, the output is an aligned, human-readable summary of scores, boxes, and
the grounded explanation trace. Formatting helpers are kept pure so they can be
tested without touching stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from evaluation.targets import TARGETS
from fingerprint import compute_fingerprint
from optimize import optimize_scene
from schemas import FingerprintResponse, OptimizeRequest, OptimizeResponse, Scene

# Named target canvases mirror the evaluation matrix so the CLI and the harness
# speak the same vocabulary; --width/--height always override a preset.
TARGET_PRESETS = {t.name: (t.width, t.height) for t in TARGETS}


def load_scene(path: Path) -> Scene:
    """Validate a scene JSON file into a :class:`Scene` (raises on malformed input)."""
    return Scene.model_validate_json(path.read_text())


def format_fingerprint(response: FingerprintResponse) -> str:
    """Render fingerprint scores and notes as a human-readable block (pure)."""
    rows = ["gene fingerprint (geometric proxy — not a perceptual score):", ""]
    for gene, score in response.scores.items():
        rows.append(f"  {gene:14} {score:6.4f}")
    rows.append("")
    rows.extend(f"note: {note}" for note in response.notes)
    return "\n".join(rows)


def format_optimize(response: OptimizeResponse) -> str:
    """Render target, placed boxes, drift, and the explanation trace (pure)."""
    target = response.target
    rows = [
        f"solver: {response.solverKind}  target: {target.width:g}x{target.height:g}",
        "",
        f"{'id':20} {'x':>7} {'y':>7} {'w':>7} {'h':>7} {'rot':>6}",
        "-" * 58,
    ]
    for box in response.boxes:
        rows.append(
            f"{box.id:20} {box.x:7.4f} {box.y:7.4f} "
            f"{box.width:7.4f} {box.height:7.4f} {box.rotation:6.1f}"
        )
    rows.append("")
    rows.append("gene drift (geometric proxy — not a quality claim):")
    for gene, drift in response.geneDrift.items():
        rows.append(f"  {gene:14} {drift:6.4f}")
    rows.append("")
    rows.append("explanation trace:")
    for step in response.explanation:
        rows.append(f"  [{step.code}] {step.message}")
    return "\n".join(rows)


def _resolve_target(args: argparse.Namespace) -> tuple[float, float]:
    """Pick target dimensions from an explicit size or a named preset."""
    if args.width is not None and args.height is not None:
        return args.width, args.height
    if args.target is not None:
        return TARGET_PRESETS[args.target]
    raise SystemExit("optimize: provide --target NAME or both --width and --height")


def _cmd_fingerprint(args: argparse.Namespace) -> int:
    response = compute_fingerprint(load_scene(args.scene))
    print(response.model_dump_json(indent=2) if args.json else format_fingerprint(response))
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    width, height = _resolve_target(args)
    request = OptimizeRequest(
        scene=load_scene(args.scene),
        targetWidth=width,
        targetHeight=height,
        margin=args.margin,
    )
    response = optimize_scene(request)
    print(response.model_dump_json(indent=2) if args.json else format_optimize(response))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="layoutdna",
        description="Run the LayoutDNA solver on a scene JSON file, no server required.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fp = sub.add_parser("fingerprint", help="compute the six proxy gene scores for a scene")
    fp.add_argument("scene", type=Path, help="path to a scene JSON file")
    fp.add_argument("--json", action="store_true", help="emit the raw API response as JSON")
    fp.set_defaults(func=_cmd_fingerprint)

    op = sub.add_parser("optimize", help="reflow a scene into a target canvas")
    op.add_argument("scene", type=Path, help="path to a scene JSON file")
    op.add_argument(
        "--target",
        choices=sorted(TARGET_PRESETS),
        help="named target preset (overridden by --width/--height)",
    )
    op.add_argument("--width", type=float, help="target canvas width in pixels")
    op.add_argument("--height", type=float, help="target canvas height in pixels")
    op.add_argument(
        "--margin", type=float, default=0.04, help="safe-area margin in [0, 0.5) (default 0.04)"
    )
    op.add_argument("--json", action="store_true", help="emit the raw API response as JSON")
    op.set_defaults(func=_cmd_optimize)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
