"""Builder CLI: print pipeline status and available operations."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Builder pipeline status (no effects, no authorization)."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the declared pipeline operations from build.yaml.",
    )
    args = parser.parse_args()
    info = {
        "skill": "builder",
        "pipeline_id": "builder.build",
        "operations": ["builder.receive_candidate", "builder.prepare_handoff"],
        "policy": {"executes_effects": False, "issues_approval": False},
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
