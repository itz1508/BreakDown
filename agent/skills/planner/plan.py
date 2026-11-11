"""Run Planner-owned Scanner capabilities through the authoritative host."""

from __future__ import annotations

from contracts.workflow.system.host import HostDispatchEnvelope
from contracts.workflow.planner.scanner import ScannerResult
from system.host.skill_dispatch import PlanningArguments, SkillContext


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: PlanningArguments) -> ScannerResult:
    """Dispatch the exact candidate to HostController; no skill-issued receipts."""
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
