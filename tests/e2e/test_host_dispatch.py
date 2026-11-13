"""Host-assigned role dispatch: exact routing, automatic work and return validation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import BaseModel

from agent.skills.planner.contracts.work_todo import WorkStatus
from agent.skills.researcher.contracts.research import Requirement, ResearchRecord
from agent.skills.shared.contracts.workflow.common import ArtifactRef
from agent.skills.shared.contracts.workflow.system.host import HostDispatchEnvelope, HostDispatchResult
from agent.skills.shared.host.sys_controller import HostController, Stage, TransitionError
from agent.skills.shared.storage.canonical_serialization import SERIALIZER_PROFILE
from tests.e2e.test_real_workflow import _advance_with_receipt


class _TaskInput(BaseModel):
    task_id: str
    text: str
    purpose: str = "research"


def _create_task(host: HostController, objective: str) -> tuple[str, str, ArtifactRef]:
    """Create a task the host-owned way: persist the input artifact, then init_task."""
    task_id = uuid4().hex
    run_id = f"run-{task_id}"
    record = _TaskInput(task_id=task_id, text=objective)
    digest = host.artifact_store.put_immutable(record, f"input:{task_id}", 1, "task_input", "1.0")
    host.init_task(task_id, run_id)
    host.event_store.append(task_id, "input_persisted", "input revision 1")
    input_ref = ArtifactRef(
        artifact_id=f"input:{task_id}",
        artifact_revision=1,
        artifact_digest=digest,
        contract_id="task_input",
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )
    return task_id, run_id, input_ref


def _research_output(host: HostController, task_id: str, run_id: str) -> ArtifactRef:
    record = ResearchRecord(
        task_id=task_id,
        run_id=run_id,
        stage_revision=1,
        requirements=(
            Requirement(
                requirement_id="REQ-001",
                source_reference="submitted-task",
                original_wording="Inspect real repository files",
                statement="Inspect real repository files",
            ),
        ),
    )
    digest = host.artifact_store.put_immutable(record, f"research-result-{task_id}", 1, "research_record", "1.0")
    return ArtifactRef(
        artifact_id=f"research-result-{task_id}",
        artifact_revision=1,
        artifact_digest=digest,
        contract_id="research_record",
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def test_host_creates_and_persists_routing_and_todo_before_dispatch(tmp_path) -> None:
    host = HostController(str(tmp_path))
    task_id, run_id, input_ref = _create_task(host, "Inspect real repository files")
    envelope, dispatch_ref, todo_ref = host.prepare_agent_dispatch(
        task_id, input_ref, "Inspect real repository files", requested_role="researcher"
    )
    assert envelope.task_id == task_id
    assert envelope.run_id == run_id
    assert envelope.role == "researcher"
    assert envelope.stage == "research"
    assert envelope.request_id
    assert envelope.request_revision == 1
    assert envelope.respond_to == "workflow_entry"
    assert (
        host.artifact_store.get_digest(dispatch_ref.artifact_id, dispatch_ref.artifact_revision)
        == dispatch_ref.artifact_digest
    )
    assert (
        HostDispatchEnvelope.model_validate_json(
            host.artifact_store.get_verified(dispatch_ref.artifact_id, dispatch_ref.artifact_revision)
        )
        == envelope
    )
    host.verify_agent_dispatch(envelope)
    assert host.work_todos.read(todo_ref).actions[0].status is WorkStatus.PENDING
    assert host.get_state(task_id).active_work_artifact_id == todo_ref.artifact_id


def test_missing_invalid_and_mismatched_envelopes_rejected(tmp_path) -> None:
    host = HostController(str(tmp_path))
    task_id, _, input_ref = _create_task(host, "Inspect real repository files")
    with pytest.raises(TransitionError, match="incorrect agent role"):
        host.prepare_agent_dispatch(task_id, input_ref, "Inspect", requested_role="builder")
    assert any(event["event_type"] == "agent_dispatch_rejected" for event in host.event_store.list(task_id))
    assert host.get_state(task_id).current_stage is Stage.RESEARCH
    with pytest.raises(TransitionError, match="Research requester"):
        host.prepare_agent_dispatch(task_id, input_ref, "Inspect", requester_role="builder")
    with pytest.raises(TransitionError, match="digest mismatch"):
        host.prepare_agent_dispatch(
            task_id, input_ref.model_copy(update={"artifact_digest": "f" * 64}), "Inspect"
        )
    envelope, _, _ = host.prepare_agent_dispatch(task_id, input_ref, "Inspect", requested_role="researcher")
    for field, value in (
        ("task_id", "other-task"),
        ("run_id", "other-run"),
        ("role", "builder"),
        ("stage", "build"),
        ("respond_to", "planner"),
        ("request_revision", 4),
    ):
        with pytest.raises(TransitionError):
            host.verify_agent_dispatch(envelope.model_copy(update={field: value}))
    with pytest.raises(ValueError):
        HostDispatchEnvelope.model_validate(
            {key: value for key, value in envelope.model_dump(mode="json").items() if key != "respond_to"}
        )


def test_host_return_validates_request_and_output_then_advances(tmp_path) -> None:
    host = HostController(str(tmp_path))
    task_id, run_id, input_ref = _create_task(host, "Inspect real repository files")
    envelope, _, todo_ref = host.prepare_agent_dispatch(
        task_id, input_ref, "Inspect real repository files"
    )
    output_ref = _research_output(host, task_id, run_id)
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
        host.receive_agent_result(
            envelope, result.model_copy(update={"output_ref": envelope.input_request_ref})
        )
    returned = host.receive_agent_result(envelope, result)
    assert host.artifact_store.get_digest(returned.artifact_id, returned.artifact_revision) == returned.artifact_digest
    _, running = host.work_todos.set_status(todo_ref, "work-1", WorkStatus.RUNNING)
    _, completed = host.work_todos.set_status(
        running, "work-1", WorkStatus.COMPLETED, actual_result="Research persisted", evidence_refs=(output_ref,)
    )
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=task_id,
        run_id=run_id,
        artifact_id=output_ref.artifact_id,
        revision=output_ref.artifact_revision,
        artifact_digest=output_ref.artifact_digest,
    )
    assert (
        host.advance_stage(
            task_id, run_id, Stage.RESEARCH, receipt, todo_ref=completed
        ).current_stage
        is Stage.AUDIT_DISCOVERY
    )
    audit, _, audit_todo = host.prepare_agent_dispatch(
        task_id, output_ref, "Discover code paths", requested_role="audit_discovery"
    )
    assert audit.role == "audit_discovery"
    assert audit.respond_to == "host_controller"
    assert host.work_todos.read(audit_todo).stage == "audit_discovery"
    with pytest.raises(TransitionError, match="incorrect agent role"):
        host.prepare_agent_dispatch(task_id, output_ref, "Attempt wrong routing", requested_role="researcher")


def test_build_stage_cannot_be_sent_to_researcher(tmp_path) -> None:
    host = HostController(tmp_path)
    host.init_task("task-001", "run-001")
    for stage in (Stage.RESEARCH, Stage.AUDIT_DISCOVERY, Stage.PLANNING, Stage.FIXTURE_VALIDATION):
        _advance_with_receipt(host, "task-001", "run-001", stage)
    assert host.get_state("task-001").current_stage is Stage.BUILD
    with pytest.raises(TransitionError, match="incorrect agent role"):
        host.prepare_agent_dispatch(
            "task-001",
            ArtifactRef(
                artifact_id="missing",
                artifact_revision=1,
                artifact_digest="f" * 64,
                contract_id="fixture",
                contract_version="1.0",
                serializer_profile=SERIALIZER_PROFILE,
            ),
            "Implement admitted actions",
            requested_role="researcher",
        )
