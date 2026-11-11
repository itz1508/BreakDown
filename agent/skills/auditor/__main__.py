"""Auditor CLI: print pipeline status and available operations."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditor pipeline status (read-only, no modifications)."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the declared pipeline operations from audit.yaml.",
    )
    args = parser.parse_args()
    info = {
        "skill": "auditor",
        "pipeline_id": "auditor.audit",
        "operations": ["auditor.inspect_scope", "auditor.prepare_search_questions"],
        "policy": {"source_access": "read_only", "issues_approval": False},
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
