"""Analyzer CLI: print pipeline status and available operations."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyzer pipeline status (read-only, no modifications)."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the declared pipeline operations.",
    )
    args = parser.parse_args()
    info = {
        "skill": "analyzer",
        "pipeline_id": "analyzer.review",
        "operations": [
            "analyzer.review_code",
            "analyzer.review_logical",
            "analyzer.review_structure",
            "analyzer.detect_broken_path",
            "analyzer.detect_mismatch_wire",
            "analyzer.detect_miswire",
        ],
        "policy": {"source_access": "read_only", "issues_approval": False},
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())