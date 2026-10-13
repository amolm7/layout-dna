"""Command-line entry point for the evaluation harness.

``python -m evaluation`` prints a human-readable table; ``--json`` dumps the full
report dict. The process exit code is a CI gate: 0 only when every *feasible*
scene x target case is violation-free and all cases are deterministic. Cases on
extreme aspect ratios (``feasibleExpected == False``) are reported as best-effort
and never fail the gate -- see ``evaluation.feasibility`` for why.
"""

from __future__ import annotations

import argparse
import json
import sys

from .harness import run_evaluation


def violations_on_feasible(report: dict) -> int:
    """Total hard-constraint violations on cases the solver should handle cleanly."""
    return sum(
        c["violations"]["total"] for c in report["cases"] if c["feasibleExpected"]
    )


def gate(report: dict) -> int:
    """Return a process exit code: 0 passes, 1 fails the CI gate."""
    passed = violations_on_feasible(report) == 0 and report["summary"]["allDeterministic"]
    return 0 if passed else 1


def format_table(report: dict) -> str:
    """Render the report as an aligned, human-readable table (pure, testable)."""
    header = (
        f"{'scene':20} {'target':12} {'stress':>6} {'drift':>6} "
        f"{'viol':>4} {'feas':>5} {'det':>4} {'ms':>8}"
    )
    rows = [header, "-" * len(header)]
    for c in report["cases"]:
        marker = "" if c["feasibleExpected"] else "  (infeasible-aspect, best-effort)"
        rows.append(
            f"{c['scene']:20} {c['target']:12} {c['aspectStress']:6.2f} "
            f"{c['aggregateDrift']:6.3f} {c['violations']['total']:4d} "
            f"{('yes' if c['feasibleExpected'] else 'no'):>5} "
            f"{('yes' if c['deterministic'] else 'NO'):>4} "
            f"{c['runtimeMs']:8.2f}{marker}"
        )
    s = report["summary"]
    rows.append("")
    rows.append(
        f"{s['cases']} cases | violations(all)={s['totalViolations']} "
        f"violations(feasible)={violations_on_feasible(report)} "
        f"deterministic={s['allDeterministic']} | "
        f"meanDrift={s['meanAggregateDrift']} maxDrift={s['maxAggregateDrift']}"
    )
    rows.append("")
    rows.append(report["disclaimer"])
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m evaluation",
        description="Run the LayoutDNA solver evaluation harness.",
    )
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    parser.add_argument(
        "--margin", type=float, default=0.04, help="safe-area margin in [0, 0.5) (default 0.04)"
    )
    args = parser.parse_args(argv)

    report = run_evaluation(margin=args.margin)
    print(json.dumps(report, indent=2) if args.json else format_table(report))
    return gate(report)


if __name__ == "__main__":
    sys.exit(main())
