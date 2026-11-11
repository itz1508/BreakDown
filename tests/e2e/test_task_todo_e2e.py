"""Fixture-backed TODO creation, admitted effects, and observed program execution.

The supplied BuildSpecification is an input fixture, not agent-generated Planning.
Research and Audit are synthetic upstream artifacts, not executed stages.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel

from contracts.workflow.common import ArtifactRef
from contracts.workflow.planner.specification import BuildSpecification
from contracts.workflow.planner.task_todo import Build
from contracts.workflow.planner.work_todo import PlannedAction, WorkBinding, WorkPlan, WorkStatus
from system.host.build_admission import BuildAdmission
from system.host.build_todos import compile_build
from system.host.effect_executor import EffectExecutionError, EffectExecutor
from system.host.package_lock import PackageLock
from system.host.work_todo import WorkTodoError
from system.host.workflow_control import HostController
from system.storage.artifact_store import DuplicateArtifactError
from system.storage.canonical_serialization import SERIALIZER_PROFILE, digest_raw

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "task_todo.json"


class UpstreamInput(BaseModel):
    """Explicit supplied upstream input, not a claim of executed agent work."""

    description: str


def _store(host: HostController, name: str, model: BaseModel, contract: str) -> ArtifactRef:
    digest = host.artifact_store.put_immutable(model, name, 1, contract, "1.0")
    return ArtifactRef(
        artifact_id=name,
        artifact_revision=1,
        artifact_digest=digest,
        contract_id=contract,
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def _assert_compilation(build: Build, expected: dict) -> None:
    observed = build.model_dump(mode="json")
    assert observed["todos"] == expected["todos"]
    assert observed["waves"] == expected["waves"]


def test_task_todo_to_verified_program(tmp_path: Path) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected"]
    workspace = tmp_path / "workspace"
    host = HostController(tmp_path / "state", workspace)
    specification = BuildSpecification.model_validate(fixture["specification"])
    frozen = _store(host, "frozen-spec", specification, "build_specification")

    build = compile_build(specification, frozen)
    _assert_compilation(build, expected)
    assert build.frozen_plan_ref == frozen
    assert build.build_id == f"build:{specification.spec_id}:{frozen.artifact_digest}"
    assert compile_build(specification, frozen) == build
    build_ref = _store(host, "compiled-todos", build, "build")
    assert Build.model_validate_json(host.artifact_store.get_verified("compiled-todos", 1)) == build

    # A schema-valid but semantically changed TODO must fail the independent oracle.
    changed = build.model_dump(mode="json")
    changed["todos"][0]["expected_result"] = "unrelated output"
    with pytest.raises(AssertionError):
        _assert_compilation(Build.model_validate(changed), expected)
    with pytest.raises(DuplicateArtifactError):
        _store(host, "frozen-spec", specification.model_copy(update={"objective": "changed"}), "build_specification")

    binding = WorkBinding(
        task_id="todo-e2e",
        run_id="run-1",
        stage="build",
        request_id="build-request",
        request_revision=1,
        input_request_ref=build_ref,
    )
    plan = WorkPlan(
        **binding.model_dump(),
        actions=tuple(
            PlannedAction(
                action_id=todo.todo_id,
                action=todo.title,
                expected_result=todo.expected_result,
                depends_on=todo.dependency_todo_ids,
            )
            for todo in build.todos
        ),
    )
    plan_ref = host.work_todos.persist_work_plan(plan)
    pending, progress_ref = host.work_todos.start(binding, work_plan_ref=plan_ref)
    assert [a.model_dump(include=set(PlannedAction.model_fields)) for a in pending.actions] == [
        a.model_dump() for a in plan.actions
    ]
    assert all(a.status is WorkStatus.PENDING for a in pending.actions)
    assert host.work_todos.start(binding, work_plan_ref=plan_ref) == (pending, progress_ref)
    with pytest.raises(WorkTodoError, match="dependencies"):
        host.work_todos.set_status(progress_ref, "entrypoint", WorkStatus.RUNNING)
    with pytest.raises(WorkTodoError, match="unfinished"):
        host.work_todos.require_complete(progress_ref, task_id=binding.task_id, run_id=binding.run_id, stage="build")

    # Real Host provenance and exact frozen-spec admission; not a fabricated receipt.
    research = _store(host, "supplied-research", UpstreamInput(description="supplied requirements"), "test_input")
    audit = _store(host, "supplied-audit", UpstreamInput(description="supplied source assessment"), "test_input")
    lock = PackageLock(host.artifact_store, host.receipt_store).lock("todo-e2e", research, audit, frozen)
    subject = f"{research.artifact_digest}:{audit.artifact_digest}:{frozen.artifact_digest}"
    admission = BuildAdmission(host.receipt_store, host.artifact_store).admit(
        "todo-e2e",
        lock.receipt_ref,
        tuple(a.action_id for a in specification.actions),
        subject,
        build_spec=specification,
        package_lock=lock,
    )
    executor = EffectExecutor(host.authorization, host.checkpoint_store, host.receipt_store, workspace)
    with pytest.raises(EffectExecutionError, match="not authorized"):
        executor.execute_admitted(
            action_id="unplanned",
            action_kind="create",
            admission_receipt=admission,
            target_path="unplanned.py",
            content="raise RuntimeError()",
        )
    assert not (workspace / "unplanned.py").exists()

    outputs = []
    for wave in build.waves:
        for action_id in wave:
            todo = next(item for item in build.todos if item.todo_id == action_id)
            path = todo.authorized_paths[0]
            _, running = host.work_todos.set_status(progress_ref, action_id, WorkStatus.RUNNING)
            output = executor.execute_admitted(
                action_id=action_id,
                action_kind="create",
                admission_receipt=admission,
                target_path=path,
                content=fixture["contents"][path],
            )
            outputs.append(output)
            observed = (workspace / path).read_bytes()
            assert observed == fixture["contents"][path].encode()
            assert output.post_image_digest == digest_raw(observed)
            evidence = _store(host, f"effect-{action_id}", output, "build_action_execution")
            _, progress_ref = host.work_todos.set_status(
                running,
                action_id,
                WorkStatus.COMPLETED,
                actual_result=f"Created {path}",
                evidence_refs=(evidence,),
            )
    assert [output.status.value for output in outputs] == expected["execution_statuses"]

    # Restart verifies durable TODO completion and exact input/output identity.
    restarted = HostController(host.state_root, workspace)
    completed = restarted.work_todos.require_complete(
        progress_ref,
        task_id=binding.task_id,
        run_id=binding.run_id,
        stage="build",
    )
    assert completed.input_request_ref == build_ref
    assert completed.work_plan_ref == plan_ref
    assert [a.expected_result for a in completed.actions] == [t.expected_result for t in build.todos]
    assert all(a.actual_result and a.evidence_refs for a in completed.actions)
    with pytest.raises(WorkTodoError, match="stale"):
        restarted.work_todos.require_complete(
            running,
            task_id=binding.task_id,
            run_id=binding.run_id,
            stage="build",
        )
    with pytest.raises(WorkTodoError, match="different task"):
        restarted.work_todos.require_complete(progress_ref, task_id="other-task", run_id=binding.run_id, stage="build")

    # Independent subprocess: Builder status alone cannot establish program correctness.
    verification = subprocess.run(
        [sys.executable, "-B", "main.py"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert {
        "returncode": verification.returncode,
        "stdout": verification.stdout,
        "stderr": verification.stderr,
    } == expected["verification"]
