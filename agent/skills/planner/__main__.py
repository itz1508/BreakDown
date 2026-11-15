"""Planner CLI: print pipeline status, tools, and repo scan."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Planner pipeline status and internal tools (read-only)."
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="List planner internal tools.",
    )
    parser.add_argument(
        "--repo-scan",
        action="store_true",
        help="Run repo_scan for structural checks.",
    )
    args = parser.parse_args()

    if args.repo_scan:
        from agent.skills.tools.repo_scan import repo_scan
        print(json.dumps(repo_scan(), indent=2, sort_keys=True))
        return 0

    info = {
        "skill": "planner",
        "pipeline_id": "planner.plan",
        "tools": [
            "tools/_gap_analysis.py",
            "tools/_create_task_todo.py",
            "tools/_create_plan.py",
            "../tools/repo_scan.py",
            "../tools/verify_all.py",
        ],
        "operations": [
            "planner.trace_requirements",
            "planner.inspect_patterns",
            "planner.draft_candidate",
            "planner.scan",
            "planner.record_findings",
            "planner.prepare_fixtures",
            "planner.return_candidate",
        ],
        "policy": {"can_approve_or_freeze": False},
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
