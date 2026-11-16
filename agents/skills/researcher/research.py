"""Researcher public entrypoint: programmatic callable and CLI wrapper.

Validates research request inputs against research.yaml and invokes researching.execute().
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from agents.skills.researcher.researching import ResearchContext, ResearchRequest, execute
from system.storage.artifact_store import ArtifactStore


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OneShot Researcher capability runner")
    parser.add_argument("--workspace", default=Path.cwd(), type=Path, help="Authorized workspace root")
    parser.add_argument("--state", default=Path(".oneshot-state"), type=Path, help="Record state root")
    parser.add_argument("--query", required=True, help="Research question or topic")
    parser.add_argument("--task-id", default="research-task", help="Optional task identifier")
    return parser


def run(
    workspace_root: str | Path,
    state_root: str | Path,
    query: str,
    task_id: str = "research-task",
) -> dict[str, Any]:
    """Canonical programmatic entrypoint matching skill trio contract."""
    context = ResearchContext(
        workspace_root=Path(workspace_root),
        artifact_store=ArtifactStore(Path(state_root)),
        providers=None,
    )
    request = ResearchRequest(
        task_id=task_id,
        run_id=f"{task_id}-run",
        information_needed=query,
        input_text=query,
    )
    return execute(context, request)


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args.workspace, args.state, args.query, task_id=args.task_id)
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
        return 0
    except Exception as exc:
        print(f"research error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

