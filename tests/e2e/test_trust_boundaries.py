"""Trust boundaries: receipts, revisions and filesystem authority are enforced.

Each test attempts a real bypass against real stores and asserts the host refuses
it, so a regression cannot be hidden behind a mocked collaborator.
"""

from __future__ import annotations

import pytest

from agents.skills.planner.contracts.work_todo import WorkStatus
from agents.skills.shared.contracts.workflow.system.host import ReceiptRef
from agents.skills.shared.host.sys_controller import STAGE_ORDER, HostController, Stage, TransitionError
from agents.skills.shared.host.sys_policy_enforcer import AuthorizationEngine, AuthorizationError
from agents.skills.shared.host.work_todo import WorkTodoError
from agents.skills.shared.storage.artifact_store import DuplicateArtifactError
from tests.e2e.harness import advance, bind_work, completed_work, store_artifact

pytestmark = pytest.mark.e2e

TASK_ID = "task-trust"
RUN_ID = "run-trust"


def _completed_research(host: HostController):
    for stage in STAGE_ORDER[:6]:
        advance(host, TASK_ID, RUN_ID, stage)
    return completed_work(host, TASK_ID, RUN_ID, Stage.RESEARCH)


def test_receipt_binds_exact_output_and_allows_transition(tmp_path) -> None:
    host = HostController(tmp_path)
    host.init_task(TASK_ID, RUN_ID)
    todo = _completed_research(host)
    evidence = host.work_todos.read(todo).actions[0].evidence_refs[0]
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=evidence.artifact_id,
        revision=evidence.artifact_revision,
        artifact_digest=evidence.artifact_digest,
    )
    assert host.receipt_store.get_subject(receipt.receipt_id) == (
        f"stage_complete:{TASK_ID}:{RUN_ID}:research:{evidence.artifact_id}:1:{evidence.artifact_digest}"
    )
    state = host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, receipt, todo_ref=todo)
    assert state.current_stage is Stage.REPOSITORY_RECONCILIATION


def test_forged_or_unbound_receipts_are_rejected(tmp_path) -> None:
    host = HostController(tmp_path)
    host.init_task(TASK_ID, RUN_ID)
    todo = _completed_research(host)
    evidence = host.work_todos.read(todo).actions[0].evidence_refs[0]
    genuine = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id=TASK_ID,
        run_id=RUN_ID,
        artifact_id=evidence.artifact_id,
        revision=evidence.artifact_revision,
        artifact_digest=evidence.artifact_digest,
    )
    forged = ReceiptRef(receipt_id=genuine.receipt_id, receipt_digest="f" * 64, issuer_id="host")
    with pytest.raises(TransitionError, match="unverified host provenance"):
        host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, forged, todo_ref=todo)

    _, digest = host.receipt_store.issue_verified(
        "legacy-receipt", "host", f"stage_complete:{TASK_ID}:{RUN_ID}:research"
    )
    legacy = ReceiptRef(receipt_id="legacy-receipt", receipt_digest=digest, issuer_id="host")
    with pytest.raises(TransitionError, match="invalid completion receipt"):
        host.advance_stage(TASK_ID, RUN_ID, Stage.RESEARCH, legacy, todo_ref=todo)
    assert host.get_state(TASK_ID).current_stage is Stage.RESEARCH


def test_completed_work_requires_actual_result_and_evidence(tmp_path) -> None:
    host = HostController(tmp_path)
    host.init_task(TASK_ID, RUN_ID)
    _, ref = host.work_todos.start(
        bind_work(host, TASK_ID, RUN_ID, Stage.RESEARCH, "evidence"),
        action="Inspect",
        expected_result="Evidence",
    )
    _, running = host.work_todos.set_status(ref, "work-1", WorkStatus.RUNNING)
    with pytest.raises(WorkTodoError, match="requires actual result and evidence"):
        host.work_todos.set_status(running, "work-1", WorkStatus.COMPLETED, actual_result="claimed")


def test_artifact_revisions_are_immutable(tmp_path) -> None:
    host = HostController(tmp_path)
    first = store_artifact(host, "same-id", "first")
    assert store_artifact(host, "same-id", "first") == first
    with pytest.raises(DuplicateArtifactError):
        store_artifact(host, "same-id", "second")


def test_filesystem_authority_is_rooted(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state = tmp_path / "state"
    inside = workspace / "module.py"
    inside.write_text("x = 1\n", encoding="utf-8")
    engine = AuthorizationEngine(allowed_roots=(str(workspace), str(state)))
    engine.check_path_safety(inside)
    with pytest.raises(AuthorizationError):
        engine.check_path_safety(tmp_path / "outside.py")
