"""Planner entrypoints: candidate creation intent and existing Host-bound Scanner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # ScannerResult is host-owned; skill-side uses Any until host provides it.
    from typing import Any as ScannerResult

    from agent.contracts.host import HostDispatchEnvelope


class PlanningPipelineNotActive(RuntimeError):
    """The declared planning pipeline has no trusted execution adapter yet."""


def create(request: object, context: object) -> Any:
    """Do not create a candidate until approved operations are truly installed."""
    if request is None or context is None:
        raise ValueError("planning.create requires a request and context")
    raise PlanningPipelineNotActive(
        "plan.yaml is declarative; a trusted, separately approved pipeline "
        "executor is required before planning.create can produce candidates"
    )


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: PlanningArguments) -> ScannerResult:
    """Preserve the existing Host-owned Scanner path."""
    scan = arguments.scan
    if scan.run_id != envelope.run_id:
        raise ValueError("Planner scan run does not match the persisted assignment")
    return context.host.scan_planning_candidate(
        task_id=envelope.task_id,
        run_id=envelope.run_id,
        candidate_ref=scan.candidate_ref,
        repository_identity=scan.repository_identity,
        capabilities=scan.capabilities,
        gap_result_ref=scan.gap_result_ref,
        gap_receipt_ref=scan.gap_receipt_ref,
    )
