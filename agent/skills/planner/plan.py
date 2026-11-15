"""Planner skill entry point.

Run: uv run --no-sync python -m agent.skills.planner.run <repository-root>
"""

from __future__ import annotations

from agent.contracts.common import ArtifactRef
from agent.contracts.host import HostDispatchEnvelope, HostDispatchResult
from agent.skills.planner.tools import (
    scan_candidate,
)


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m agent.skills.planner.run <repository-root>")
        sys.exit(1)

    repo_root = sys.argv[1]

    # Run a basic scan to demonstrate planner capabilities
    candidate_ref = ArtifactRef(
        artifact_id=repo_root,
        artifact_revision=1,
        artifact_digest="",
        contract_id="planning",
        contract_version="1.0",
        serializer_profile="rfc8785-jcs-sha256-v1",
    )
    result = scan_candidate(
        candidate_ref=candidate_ref,
        repository_identity=repo_root,
        capabilities=("syntax", "imports", "types", "security", "paths", "coverage"),
    )

    print(f"Planning candidate: {result.request_id}")
    print(f"Requested capabilities: {', '.join(result.capabilities_checked)}")
    print(f"Executed capabilities: {', '.join(result.capabilities_checked)}")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  - {f.capability}: {f.message}")


if __name__ == "__main__":
    main()


def pre_dispatch(request: HostDispatchEnvelope) -> HostDispatchEnvelope:
    """Validate and enrich the request before Planner execution."""
    if request.stage != "planning":
        raise ValueError(f"Planner skill can only operate at stage 'planning', got '{request.stage}'.")
    if request.requester_role not in ("host", "planner", "auditor"):
        raise ValueError(f"Planner skill rejects requests from unauthorized role '{request.requester_role}'.")
    enriched = request.model_copy(
        update={
            "information_needed": (
                request.information_needed + " | planner_scope: code_review_design_scanner_gap_resolution"
            )
        }
    )
    return enriched


def post_dispatch(result: HostDispatchResult) -> HostDispatchResult:
    """Verify Planner result after execution."""
    if not result.output_ref.artifact_id:
        raise ValueError("Planner result must reference an output artifact.")
    if result.output_ref.contract_id not in (
        "planning_record",
        "build_specification",
    ):
        raise ValueError(
            f"Planner output must use contract 'planning_record' or "
            f"'build_specification', got '{result.output_ref.contract_id}'."
        )
    return result


__all__ = ["post_dispatch", "pre_dispatch"]
