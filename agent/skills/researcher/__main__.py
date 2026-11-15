"""Researcher CLI: print pipeline status and available operations."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Researcher pipeline status (read-only, no retrieval)."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the declared pipeline operations from research.yaml.",
    )
    args = parser.parse_args()
    info = {
        "skill": "researcher",
        "pipeline_id": "researcher.research",
        "segments": {
            "review": ["researcher.review_search", "researcher.prepare_query"],
            "retrieve": ["researcher.compound_retrieve", "researcher.expand_sources", "researcher.verify_lineage"],
            "main": ["researcher.retrieve_evidence", "researcher.investigate", "researcher.record_evidence"],
        },
        "limits": {"max_depth": 2, "max_candidates": 50, "max_records": 200},
        "policy": {
            "retrieval_requires_external_authorization": True,
            "relevance_is_not_evidence": True,
            "source_access": "read_only",
            "can_approve_plan": False,
        },
    }
    print(json.dumps(info, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
