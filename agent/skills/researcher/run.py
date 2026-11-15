"""Researcher skill entry point.

Run: uv run --no-sync python -m agent.skills.researcher.run <repository-root>
"""

from __future__ import annotations

from agent.contracts.host import HostDispatchEnvelope, HostDispatchResult
from agent.skills.researcher.tools.research_catalog import build_catalog

__all__ = ["build_catalog", "post_dispatch", "pre_dispatch"]


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m agent.skills.researcher.run <repository-root>")
        sys.exit(1)

    repo_root = sys.argv[1]

    catalog = build_catalog(repo_root=repo_root)

    print(f"Catalog entries: {len(catalog)}")
    for entry in catalog:
        print(f"  - {entry.get('type', 'unknown')}: {entry.get('description', 'no description')}")


def pre_dispatch(request: HostDispatchEnvelope) -> HostDispatchEnvelope:
    """Validate and enrich the request before Researcher execution."""
    if request.stage != "research":
        raise ValueError(f"Researcher skill can only operate at stage 'research', got '{request.stage}'.")
    if request.requester_role not in ("host", "researcher"):
        raise ValueError(f"Researcher skill rejects requests from unauthorized role '{request.requester_role}'.")
    enriched = request.model_copy(
        update={
            "information_needed": (
                request.information_needed + " | researcher_scope: research_execution_sourced_claims"
            )
        }
    )
    return enriched


def post_dispatch(result: HostDispatchResult) -> HostDispatchResult:
    """Verify Researcher result after execution."""
    if not result.output_ref.artifact_id:
        raise ValueError("Researcher result must reference an output artifact.")
    if result.output_ref.contract_id != "research_record":
        raise ValueError(
            f"Researcher output must use contract 'research_record', got '{result.output_ref.contract_id}'."
        )
    return result


__all__ = ["post_dispatch", "pre_dispatch"]
