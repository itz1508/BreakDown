"""Planner public entrypoint: programmatic callable and CLI wrapper.

Validates planning request inputs against plan.yaml and delegates to planning.create().
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from agents.skills.planner.planning import PlanningPipelineNotActive, create


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OneShot Planner capability runner")
    parser.add_argument("--request", required=True, help="Planning request or objective description")
    parser.add_argument("--workspace", default=Path.cwd(), type=Path, help="Authorized workspace root")
    parser.add_argument("--evidence", default="", help="Optional evidence reference or digest")
    return parser


def run(request_text: str, workspace_root: str | Path = ".", evidence_ref: str = "") -> Any:
    """Canonical programmatic entrypoint matching skill trio contract."""
    context = {"workspace": str(workspace_root), "evidence": evidence_ref}
    return create(request_text, context)


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        run(args.request, workspace_root=args.workspace, evidence_ref=args.evidence)
        return 0
    except PlanningPipelineNotActive as exc:
        print(f"planning pipeline inactive: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"planning error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

