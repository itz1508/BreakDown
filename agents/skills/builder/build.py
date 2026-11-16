"""Build entry point: programmatic callable and CLI wrapper for build execution.

Modeled after PEPs build.py (direct CLI parser, SDK/library wrapper, clean exit codes).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agents.skills.builder.building import execute_build


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OneShot Build Executor")
    parser.add_argument("--plan", required=True, type=Path, help="Path to approved plan JSON/YAML")
    parser.add_argument("--workspace", default=Path.cwd(), type=Path, help="Workspace target root")
    parser.add_argument("--state", default=Path(".oneshot-state"), type=Path, help="Record state root")
    parser.add_argument("--dry-run", action="store_true", help="Validate plan without applying file modifications")
    return parser


def run(
    plan_path: str | Path,
    workspace_root: str | Path = ".",
    state_root: str | Path = ".oneshot-state",
    dry_run: bool = False,
) -> int:
    """Canonical programmatic entrypoint matching skill trio contract."""
    result = execute_build(Path(plan_path), Path(workspace_root), Path(state_root), dry_run=dry_run)
    return 0 if result.get("status") == "completed" else 1


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        return run(args.plan, args.workspace, args.state, dry_run=args.dry_run)
    except Exception as exc:
        print(f"build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

