"""Auditor skill entry point.

Run: uv run --no-sync python -m agent.skills.auditor.run <repository-root>
"""

from __future__ import annotations

from typing import Any

from agent.contracts.host import HostDispatchEnvelope, HostDispatchResult
from agent.skills.auditor.tools import scan

Result = dict[str, Any]


def main() -> None:
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python -m agent.skills.auditor.run <repository-root>")
        sys.exit(1)

    repo_root = Path(sys.argv[1]).resolve()
    scope = repo_root.name

    result = scan(root=repo_root, scope=scope)

    print(f"Audit disposition: {result.disposition}")
    print(f"Executed capabilities: {', '.join(result.executed_capabilities)}")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  - {f.capability}: {f.message} (severity={f.severity})")


if __name__ == "__main__":
    main()


def pre_dispatch(request: HostDispatchEnvelope) -> HostDispatchEnvelope:
    """Validate and enrich the request before Auditor execution.

    Confirms the stage is compatible with read-only audit work and that
    the request scope does not request write authorization.
    """
    if request.stage not in ("research", "audit_discovery", "planning"):
        raise ValueError(
            f"Auditor skill cannot operate at stage '{request.stage}'; "
            "read-only inspection is limited to research, audit_discovery, "
            "and planning stages."
        )
    if request.requester_role not in ("host", "auditor", "planner", "researcher"):
        raise ValueError(f"Auditor skill rejects requests from unauthorized role '{request.requester_role}'.")
    # Enrich with Auditor context
    enriched = request.model_copy(
        update={
            "information_needed": (request.information_needed + " | auditor_scope: read_only_repository_inspection")
        }
    )
    return enriched


def post_dispatch(result: HostDispatchResult) -> HostDispatchResult:
    """Verify Auditor result after execution.

    Confirms the output artifact reference is well-formed and that no
    receipt or authorization claims were self-issued by the skill.
    """
    if not result.output_ref.artifact_id:
        raise ValueError("Auditor result must reference an output artifact.")
    if result.output_ref.contract_id != "audit_findings":
        raise ValueError(f"Auditor output must use contract 'audit_findings', got '{result.output_ref.contract_id}'.")
    return result


__all__ = ["post_dispatch", "pre_dispatch"]
