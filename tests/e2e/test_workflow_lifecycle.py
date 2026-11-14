"""Whole-workflow E2E: the full v3 stage flow, dispatch routing and restart durability.

These tests drive the same HostController the runtime uses. They never call a
stage "done" without host-assigned work, persisted evidence and a bound receipt.
"""

from __future__ import annotations

import pytest

from agent.cli import cmd_verify
from agent.skills.planner.contracts.work_todo import WorkStatus
from agent.skills.shared.contracts.workflow.system.host import HostDispatchResult
from agent.skills.shared.host.sys_controller import STAGE_ORDER, HostController, Stage, TransitionError
from tests.e2e.harness import (
    advance,
    bind_work,
    completed_work,
    create_task,
    research_output,
    store_artifact,
)

pytestmark = pytest.mark.e2e

TASK_ID = "task-e2e"
RUN_ID = "run-e2e"
OBJECTIVE = "Inspect real repository files"


def test_full_workflow_completes_and_survives_restart(tmp_path) -> None:
    host = HostController(tmp_path / "state")
    create_task(host, TASK_ID, RUN_ID, OBJECTIVE)

    for stage in STAGE_ORDER[:-1]:
        state = advance(host, TASK_ID, RUN_ID, stage)
        assert state.current_stage is STAGE_ORDER[STAGE_ORDER.index(stage) + 1]
        assert stage in state.completed_stages
    assert host.get_state(TASK_ID).current_stage is Stage.COMPLETION_AND_RETENTION

    with pytest.raises(TransitionError, match="receipt required"):
        host.complete_final_stage(TASK_ID, RUN_ID, None, todo_ref=None)
    evidence = store_artifact(host, f"output-{TASK_ID}-completion", "workflow complete")
    final_receipt = host.issue_stage_receipt(
        Stage.COMPLETION_AND_RETENTION,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=evidence.artifact_id,
        revision=evidence.artifact_revision,
        artifact_digest=evidence.artifact_digest,
    )
    completed = host.complete_final_stage(TASK_ID, RUN_ID, final_receipt, todo_ref=None)
    assert set(completed.completed_stages) == set(STAGE_ORDER)
    assert cmd_verify(TASK_ID, state_root=str(tmp_path / "state")) == 0

    # A fresh controller must recover the same durable state, not a fresh workflow.
    restarted = HostController(tmp_path / "state")
    recovered = restarted.get_state(TASK_ID)
    assert recovered is not None
    assert set(recovered.completed_stages) == set(STAGE_ORDER)
    evidence = restarted.artifact_store.get_verified(f"output-{TASK_ID}-completion", 1)
    assert evidence


def test_stage_advance_requires_host_assigned_completed_work(tmp_path) -> None:
    host = HostController(tmp_path)
    create_task(host, TASK_ID, RUN_ID, OBJECTIVE)
    for stage in STAGE_ORDER[:6]:
        advance(host, TASK_ID, RUN_ID, stage)

    with pytest.raises(TransitionError, match="receipt required"):
        host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH)

    # Work started without a host assignment cannot close the stage, even when the
    # receipt is bound to that work's own evidence.
    _, unassigned = host.work_todos.start(
        bind_work(host, TASK_ID, RUN_ID, Stage.RESEARCH, "unassigned"),
        action="Inspect without a host assignment",
        expected_result="Evidence",
    )
    _, running = host.work_todos.set_status(unassigned, "work-1", WorkStatus.RUNNING)
    evidence = store_artifact(host, "evidence-unassigned", "unassigned observation")
    _, completed = host.work_todos.set_status(
        running, "work-1", WorkStatus.COMPLETED, actual_result="observed", evidence_refs=(evidence,)
    )
    unassigned_evidence = host.work_todos.read(completed).actions[0].evidence_refs[0]
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=unassigned_evidence.artifact_id,
        revision=unassigned_evidence.artifact_revision,
        artifact_digest=unassigned_evidence.artifact_digest,
    )
    with pytest.raises(TransitionError, match="host-assigned"):
        host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, receipt, todo_ref=completed)

    # Work assigned to the stage, but the receipt points at a different artifact.
    assigned = completed_work(host, TASK_ID, RUN_ID, Stage.RESEARCH)
    unrelated = store_artifact(host, "unrelated-output", "not this work")
    unrelated_receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=unrelated.artifact_id,
        revision=unrelated.artifact_revision,
        artifact_digest=unrelated.artifact_digest,
    )
    with pytest.raises(TransitionError, match="evidence not in completed work"):
        host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, unrelated_receipt, todo_ref=assigned)
    assert host.get_state(TASK_ID).current_stage is Stage.RESEARCH


def test_dispatch_routing_and_return_are_exact(tmp_path) -> None:
    host = HostController(str(tmp_path))
    input_ref = create_task(host, TASK_ID, RUN_ID, OBJECTIVE)
    for stage in STAGE_ORDER[:6]:
        advance(host, TASK_ID, RUN_ID, stage)
    envelope, dispatch_ref, todo_ref = host.prepare_agent_dispatch(
        TASK_ID, input_ref, "Inspect real repository files", requested_role="researcher"
    )
    assert (envelope.task_id, envelope.run_id, envelope.role, envelope.stage) == (
        TASK_ID,
        RUN_ID,
        "researcher",
        "research",
    )
    assert envelope.respond_to == "workflow_entry"
    assert host.artifact_store.get_digest(dispatch_ref.artifact_id, dispatch_ref.artifact_revision) == (
        dispatch_ref.artifact_digest
    )
    assert host.work_todos.read(todo_ref).stage == "research"

    output_ref = research_output(host, TASK_ID, RUN_ID, OBJECTIVE)
    result = HostDispatchResult(
        task_id=envelope.task_id,
        run_id=envelope.run_id,
        stage=envelope.stage,
        role=envelope.role,
        request_id=envelope.request_id,
        request_revision=envelope.request_revision,
        respond_to=envelope.respond_to,
        output_ref=output_ref,
    )
    for field, value in (
        ("request_id", "wrong-request"),
        ("request_revision", 4),
        ("role", "builder"),
        ("respond_to", "planning"),
    ):
        with pytest.raises(TransitionError, match="routing mismatch"):
            host.receive_agent_result(envelope, result.model_copy(update={field: value}))
    with pytest.raises(TransitionError, match="output contract"):
        host.receive_agent_result(envelope, result.model_copy(update={"output_ref": envelope.input_request_ref}))

    returned = host.receive_agent_result(envelope, result)
    assert host.artifact_store.get_digest(returned.artifact_id, returned.artifact_revision) == returned.artifact_digest
    _, running = host.work_todos.set_status(todo_ref, "work-1", WorkStatus.RUNNING)
    _, finished = host.work_todos.set_status(
        running, "work-1", WorkStatus.COMPLETED, actual_result="Research persisted", evidence_refs=(output_ref,)
    )
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=output_ref.artifact_id,
        revision=output_ref.artifact_revision,
        artifact_digest=output_ref.artifact_digest,
    )
    assert host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, receipt, todo_ref=finished).current_stage is (
        Stage.REPOSITORY_RECONCILIATION
    )

    audit, _, audit_todo = host.prepare_agent_dispatch(
        TASK_ID, output_ref, "Reconcile repository evidence", requested_role="auditor"
    )
    assert audit.respond_to == "host_controller"
    assert host.work_todos.read(audit_todo).stage == "repository_reconciliation"
    with pytest.raises(TransitionError, match="incorrect agent role"):
        host.prepare_agent_dispatch(TASK_ID, output_ref, "Attempt wrong routing", requested_role="researcher")
