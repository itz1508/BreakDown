"""Real host fixtures for the E2E suite.

Every helper writes through HostController: artifacts, receipts, work todos and
stage transitions are the same objects production code uses. No helper reports a
stage as complete unless the host accepted persisted evidence for it.
"""

from __future__ import annotations

from pydantic import BaseModel

from agents.skills.planner.contracts.work_todo import WorkBinding, WorkStatus
from agents.skills.researcher.contracts.research import Requirement, ResearchRecord
from agents.skills.shared.contracts.workflow.common import ArtifactRef
from agents.skills.shared.host.sys_controller import DISPATCH_STAGES, HostController, Stage
from agents.skills.shared.storage.canonical_serialization import SERIALIZER_PROFILE
from tests.fixtures.planning import artifact_ref, make_planning_record
from tests.fixtures.structural_gap import passing_gap


class Evidence(BaseModel):
    """Opaque persisted payload; only its digest and revision matter to the host."""

    label: str


class TaskInput(BaseModel):
    """Submitted task payload; persisted before the host may own the task."""

    task_id: str
    text: str
    purpose: str = "research"


def create_task(
    host: HostController,
    task_id: str,
    run_id: str,
    text: str = "Inspect real repository files",
) -> ArtifactRef:
    """Persist the submitted task, then initialize it as the host-owned workflow."""
    digest = host.artifact_store.put_immutable(
        TaskInput(task_id=task_id, text=text), f"input:{task_id}", 1, "task_input", "1.0"
    )
    host.init_task(task_id, run_id)
    host.event_store.append(task_id, "input_persisted", "input revision 1")
    return ArtifactRef(
        artifact_id=f"input:{task_id}",
        artifact_revision=1,
        artifact_digest=digest,
        contract_id="task_input",
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def research_output(host: HostController, task_id: str, run_id: str, statement: str) -> ArtifactRef:
    """Persist the Research record a dispatched researcher would return."""
    record = ResearchRecord(
        task_id=task_id,
        run_id=run_id,
        stage_revision=1,
        requirements=(
            Requirement(
                requirement_id="REQ-001",
                source_reference="submitted-task",
                original_wording=statement,
                statement=statement,
            ),
        ),
    )
    name = f"research-result-{task_id}"
    digest = host.artifact_store.put_immutable(record, name, 1, "research_record", "1.0")
    return ArtifactRef(
        artifact_id=name,
        artifact_revision=1,
        artifact_digest=digest,
        contract_id="research_record",
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def prepare_planning_candidate(host: HostController, task_id: str, run_id: str) -> ArtifactRef:
    """Store a planning record and move the task checkpoint to the gap-check stage.

    The complete upstream workflow is not executed here. This is the one
    documented fixture boundary the CLI Scanner adapter test needs, and it is
    kept in one place so the substitution stays visible.
    """
    checkpoint = host.checkpoint_store.load_checkpoint(task_id)
    assert checkpoint is not None
    revision, state, _ = checkpoint
    state["current_stage"] = "specification_gap_check"
    host.checkpoint_store.checkpoint_cas(task_id, revision, state)
    planning = make_planning_record().model_copy(update={"task_id": task_id, "run_id": run_id})
    digest = host.artifact_store.put_immutable(planning, f"candidate:{task_id}", 1, "planning", "1.0")
    return artifact_ref(f"candidate:{task_id}", 1, digest)


def store_model(
    host: HostController,
    artifact_id: str,
    model: BaseModel,
    contract_id: str,
    contract_version: str = "1.0",
) -> ArtifactRef:
    """Persist any model at revision 1 and return its exact artifact reference."""
    digest = host.artifact_store.put_immutable(model, artifact_id, 1, contract_id, contract_version)
    return ArtifactRef(
        artifact_id=artifact_id,
        artifact_revision=1,
        artifact_digest=digest,
        contract_id=contract_id,
        contract_version=contract_version,
        serializer_profile=SERIALIZER_PROFILE,
    )


def store_artifact(
    host: HostController,
    artifact_id: str,
    label: str,
    contract_id: str = "fixture",
) -> ArtifactRef:
    return store_model(host, artifact_id, Evidence(label=label), contract_id)


def bind_work(host: HostController, task_id: str, run_id: str, stage: Stage, label: str) -> WorkBinding:
    request = store_artifact(host, f"input-{label}", f"Assigned work: {stage.value}")
    return WorkBinding(
        task_id=task_id,
        run_id=run_id,
        stage=stage.value,
        request_id=label,
        request_revision=1,
        input_request_ref=request,
    )


def completed_work(
    host: HostController, task_id: str, run_id: str, stage: Stage, label: str | None = None
) -> ArtifactRef:
    """Assign work to this stage and finish it with real persisted evidence."""
    label = label or f"work-{stage.value}"
    todo, ref = host.assign_work(
        bind_work(host, task_id, run_id, stage, label),
        action=f"Observe {stage.value}",
        expected_result=f"Evidence for {stage.value}",
    )
    assert len(todo.actions) == 1
    _, running = host.work_todos.set_status(ref, "work-1", WorkStatus.RUNNING)
    evidence = store_artifact(host, f"evidence-{label}", f"observed {stage.value}")
    _, done = host.work_todos.set_status(
        running,
        "work-1",
        WorkStatus.COMPLETED,
        actual_result=f"observed {stage.value}",
        evidence_refs=(evidence,),
    )
    return done


def advance(host: HostController, task_id: str, run_id: str, stage: Stage):
    """Complete one non-final stage exactly the way the workflow requires."""
    if stage in DISPATCH_STAGES:
        todo = completed_work(host, task_id, run_id, stage)
        receipt = host.issue_stage_receipt(stage, task_id=task_id, run_id=run_id, revision=1)
    else:
        todo = None
        evidence = store_artifact(host, f"output-{task_id}-{stage.value}", f"recorded {stage.value}")
        receipt = host.issue_stage_receipt(
            stage,
            task_id=task_id,
            run_id=run_id,
            artifact_id=evidence.artifact_id,
            revision=evidence.artifact_revision,
            artifact_digest=evidence.artifact_digest,
        )
    kwargs: dict[str, object] = {}
    if todo is not None:
        kwargs["todo_ref"] = todo
    if stage is Stage.SPECIFICATION_GAP_CHECK:
        gap = passing_gap(host, task_id, run_id)
        assert gap.completion_receipt_ref is not None
        kwargs["gap_result_ref"] = gap.result_ref
        kwargs["gap_receipt_ref"] = gap.completion_receipt_ref
    if stage is Stage.USER_REVIEW_AND_APPROVAL:
        kwargs["approval_ref"] = store_artifact(
            host, f"approval-{task_id}", "exact plan approved", contract_id="approved_plan"
        )
    return host.advance_stage(task_id, run_id, stage, receipt, **kwargs)
