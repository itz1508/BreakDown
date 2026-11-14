"""Compiled TaskTodo to admitted effects to an independently verified program.

The BuildSpecification is a supplied input fixture; Research and Audit are not
executed stages here. Everything after that fixture boundary is real: compilation,
package lock, admission, effects on disk, restart checks and a subprocess run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic import BaseModel

from agent.skills.builder.build_admission import BuildAdmission
from agent.skills.builder.build_todos import compile_build
from agent.skills.builder.effect_executor import EffectExecutionError, EffectExecutor
from agent.skills.builder.package_lock import PackageLock
from agent.skills.planner.contracts.specification import BuildSpecification
from agent.skills.planner.contracts.task_todo import Build
from agent.skills.planner.contracts.work_todo import PlannedAction, WorkBinding, WorkPlan, WorkStatus
from agent.skills.shared.contracts.workflow.common import ArtifactRef
from agent.skills.shared.host.sys_controller import HostController
from agent.skills.shared.host.work_todo import WorkTodoError
from agent.skills.shared.storage.artifact_store import DuplicateArtifactError
from agent.skills.shared.storage.canonical_serialization import digest_raw
from tests.e2e.harness import store_model

pytestmark = pytest.mark.e2e

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "task_todo.json"
TASK_ID = "todo-e2e"
RUN_ID = "run-1"


class UpstreamInput(BaseModel):
    """Explicit supplied upstream input, not a claim of executed agent work."""

    description: str


@dataclass(frozen=True)
class BuildScenario:
    """One real build workspace, its frozen plan and its admission."""

    host: HostController
    workspace: Path
    fixture: dict
    expected: dict
    specification: BuildSpecification
    frozen: ArtifactRef
    build: Build
    build_ref: ArtifactRef
    binding: WorkBinding
    plan: WorkPlan
    plan_ref: ArtifactRef
    pending: object
    progress_ref: ArtifactRef
    admission: object
    executor: EffectExecutor


def assert_compilation_matches_oracle(build: Build, expected: dict) -> None:
    observed = build.model_dump(mode="json")
    assert observed["todos"] == expected["todos"]
    assert observed["waves"] == expected["waves"]


def build_scenario(tmp_path: Path) -> BuildScenario:
    """Build fresh state for one test: no artifact is shared between tests."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected"]
    workspace = tmp_path / "workspace"
    host = HostController(tmp_path / "state", workspace)
    specification = BuildSpecification.model_validate(fixture["specification"])
    frozen = store_model(host, "frozen-spec", specification, "build_specification")
    build = compile_build(specification, frozen)
    build_ref = store_model(host, "compiled-todos", build, "build")

    binding = WorkBinding(
        task_id=TASK_ID,
        run_id=RUN_ID,
        stage="sandbox_execution",
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

    # Real Host provenance and exact frozen-spec admission; not a fabricated receipt.
    research = store_model(host, "supplied-research", UpstreamInput(description="supplied requirements"), "test_input")
    audit = store_model(host, "supplied-audit", UpstreamInput(description="supplied source assessment"), "test_input")
    lock = PackageLock(host.artifact_store, host.receipt_store).lock(TASK_ID, research, audit, frozen)
    subject = f"{research.artifact_digest}:{audit.artifact_digest}:{frozen.artifact_digest}"
    admission = BuildAdmission(host.receipt_store, host.artifact_store).admit(
        TASK_ID,
        lock.receipt_ref,
        tuple(action.action_id for action in specification.actions),
        subject,
        build_spec=specification,
        package_lock=lock,
    )
    executor = EffectExecutor(host.authorization, host.checkpoint_store, host.receipt_store, workspace)
    return BuildScenario(
        host=host,
        workspace=workspace,
        fixture=fixture,
        expected=expected,
        specification=specification,
        frozen=frozen,
        build=build,
        build_ref=build_ref,
        binding=binding,
        plan=plan,
        plan_ref=plan_ref,
        pending=pending,
        progress_ref=progress_ref,
        admission=admission,
        executor=executor,
    )


def execute_waves(scenario: BuildScenario) -> tuple[list, ArtifactRef]:
    """Execute every admitted wave in order and record real evidence per action."""
    outputs = []
    progress_ref = scenario.progress_ref
    for wave in scenario.build.waves:
        for action_id in wave:
            todo = next(item for item in scenario.build.todos if item.todo_id == action_id)
            path = todo.authorized_paths[0]
            _, running = scenario.host.work_todos.set_status(progress_ref, action_id, WorkStatus.RUNNING)
            output = scenario.executor.execute_admitted(
                action_id=action_id,
                action_kind="create",
                admission_receipt=scenario.admission,
                target_path=path,
                content=scenario.fixture["contents"][path],
            )
            outputs.append(output)
            observed = (scenario.workspace / path).read_bytes()
            assert observed == scenario.fixture["contents"][path].encode()
            assert output.post_image_digest == digest_raw(observed)
            evidence = store_model(scenario.host, f"effect-{action_id}", output, "build_action_execution")
            _, progress_ref = scenario.host.work_todos.set_status(
                running,
                action_id,
                WorkStatus.COMPLETED,
                actual_result=f"Created {path}",
                evidence_refs=(evidence,),
            )
    return outputs, progress_ref


def test_task_todo_compiles_to_frozen_plan(tmp_path) -> None:
    scenario = build_scenario(tmp_path)
    assert_compilation_matches_oracle(scenario.build, scenario.expected)
    assert scenario.build.frozen_plan_ref == scenario.frozen
    assert scenario.build.build_id == f"build:{scenario.specification.spec_id}:{scenario.frozen.artifact_digest}"
    assert compile_build(scenario.specification, scenario.frozen) == scenario.build
    assert Build.model_validate_json(scenario.host.artifact_store.get_verified("compiled-todos", 1)) == scenario.build

    # A schema-valid but semantically changed entry must fail the independent oracle.
    changed = scenario.build.model_dump(mode="json")
    changed["todos"][0]["expected_result"] = "unrelated output"
    with pytest.raises(AssertionError):
        assert_compilation_matches_oracle(Build.model_validate(changed), scenario.expected)
    with pytest.raises(DuplicateArtifactError):
        store_model(
            scenario.host,
            "frozen-spec",
            scenario.specification.model_copy(update={"objective": "changed"}),
            "build_specification",
        )


def test_admitted_effects_produce_the_expected_program(tmp_path) -> None:
    scenario = build_scenario(tmp_path)
    with pytest.raises(EffectExecutionError, match="not authorized"):
        scenario.executor.execute_admitted(
            action_id="unplanned",
            action_kind="create",
            admission_receipt=scenario.admission,
            target_path="unplanned.py",
            content="raise RuntimeError()",
        )
    assert not (scenario.workspace / "unplanned.py").exists()

    outputs, _ = execute_waves(scenario)
    assert [output.status.value for output in outputs] == scenario.expected["execution_statuses"]

    # Builder status alone cannot establish program correctness.
    verification = subprocess.run(
        [sys.executable, "-B", "main.py"],
        cwd=scenario.workspace,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert {
        "returncode": verification.returncode,
        "stdout": verification.stdout,
        "stderr": verification.stderr,
    } == scenario.expected["verification"]


def test_restart_requires_exact_completion_evidence(tmp_path) -> None:
    scenario = build_scenario(tmp_path)
    assert [action.model_dump(include=set(PlannedAction.model_fields)) for action in scenario.pending.actions] == [
        action.model_dump() for action in scenario.plan.actions
    ]
    assert all(action.status is WorkStatus.PENDING for action in scenario.pending.actions)
    assert scenario.host.work_todos.start(scenario.binding, work_plan_ref=scenario.plan_ref) == (
        scenario.pending,
        scenario.progress_ref,
    )
    with pytest.raises(WorkTodoError, match="dependencies"):
        scenario.host.work_todos.set_status(scenario.progress_ref, "entrypoint", WorkStatus.RUNNING)
    with pytest.raises(WorkTodoError, match="unfinished"):
        scenario.host.work_todos.require_complete(
            scenario.progress_ref, task_id=TASK_ID, run_id=RUN_ID, stage="sandbox_execution"
        )

    _, completed_ref = execute_waves(scenario)
    restarted = HostController(scenario.host.state_root, scenario.workspace)
    completed = restarted.work_todos.require_complete(
        completed_ref, task_id=TASK_ID, run_id=RUN_ID, stage="sandbox_execution"
    )
    assert completed.input_request_ref == scenario.build_ref
    assert completed.work_plan_ref == scenario.plan_ref
    assert [action.expected_result for action in completed.actions] == [
        todo.expected_result for todo in scenario.build.todos
    ]
    assert all(action.actual_result and action.evidence_refs for action in completed.actions)
    with pytest.raises(WorkTodoError, match="stale"):
        restarted.work_todos.require_complete(
            scenario.progress_ref, task_id=TASK_ID, run_id=RUN_ID, stage="sandbox_execution"
        )
    with pytest.raises(WorkTodoError, match="different task"):
        restarted.work_todos.require_complete(
            completed_ref, task_id="other-task", run_id=RUN_ID, stage="sandbox_execution"
        )
