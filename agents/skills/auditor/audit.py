"""Auditor public entrypoint: programmatic callable and CLI wrapper.

Validates audit request inputs against audit.yaml and invokes auditing.run().
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.skills.auditor.auditing import run
from agents.skills.auditor.tools.core import CAPABILITY_ORDER, AuditResult


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OneShot Auditor capability runner")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Authorized repository root")
    parser.add_argument("--scope", default=".", help="Relative in-repository directory")
    parser.add_argument("--request", default="", help="Audit request or question")
    parser.add_argument(
        "--capability",
        action="append",
        choices=CAPABILITY_ORDER,
        default=[],
        dest="capabilities",
        help="Specific audit capability to execute (default: all)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        result: AuditResult = run(
            workspace_root=args.root,
            request=args.request,
            scope=args.scope,
            capabilities=tuple(args.capabilities),
        )
    except Exception as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 2 if result.disposition == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
