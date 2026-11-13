"""Adversarial regression tests for artifact-bound receipts and stage transitions."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from agent.host.contracts.common import ArtifactRef
from agent.host.contracts.system.host import ReceiptRef
from agent.host.storage.canonical_serialization import SERIALIZER_PROFILE
from agent.host.sys_controller import HostController, Stage, TransitionError
from agent.skills.planner.contracts.work_todo import WorkBinding, WorkStatus


class _Evidence(BaseModel):
    value: str


def _artifact(host: HostController, artifact_id: str, value: str) -> ArtifactRef:
    digest = host.artifact_store.put_immutable(_Evidence(value=value), artifact_id, 1, "fixture", "1.0")
    return ArtifactRef(
        artifact_id=artifact_id,
        artifact_revision=1,
        artifact_digest=digest,
        contract_id="fixture",
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def _completed_research_work(host: HostController, task_id: str, run_id: str) -> tuple[ArtifactRef, ArtifactRef]:
    source = _artifact(host, f"input-{task_id}", "authorized input")
    binding = WorkBinding(
        task_id=task_id,
        run_id=run_id,
        stage="research",
        request_id=f"research-{task_id}",
        request_revision=1,
        input_request_ref=source,
    )
    _, first = host.assign_work(binding, action="Inspect source", expected_result="Evidence persisted")
    _, running = host.work_todos.set_status(first, "work-1", WorkStatus.RUNNING)
    evidence = _artifact(host, f"result-{task_id}", "observed result")
    _, done = host.work_todos.set_status(
        running, "work-1", WorkStatus.COMPLETED, actual_result="Observed", evidence_refs=(evidence,)
    )
    return done, evidence


def test_receipt_binds_exact_output_and_stage_transition(tmp_path: Path) -> None:
    host = HostController(tmp_path)
    host.init_task("task-one", "run-one")
    todo, evidence = _completed_research_work(host, "task-one", "run-one")
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id="task-one",
        run_id="run-one",
        artifact_id=evidence.artifact_id,
        revision=evidence.artifact_revision,
        artifact_digest=evidence.artifact_digest,
    )
    subject = host.receipt_store.get_subject(receipt.receipt_id)
    assert subject == (f"stage_complete:task-one:run-one:research:{evidence.artifact_id}:1:{evidence.artifact_digest}")
    stage = host.advance_stage("task-one", "run-one", Stage.RESEARCH, receipt, todo_ref=todo)
    assert stage.current_stage is Stage.AUDIT_DISCOVERY


def test_legacy_stage_receipt_rejected(tmp_path: Path) -> None:
    host = HostController(tmp_path)
    host.init_task("task-one", "run-one")
    todo, _ = _completed_research_work(host, "task-one", "run-one")
    _, digest = host.receipt_store.issue_verified("old-receipt", "host", "stage_complete:task-one:run-one:research")
    old = ReceiptRef(receipt_id="old-receipt", receipt_digest=digest, issuer_id="host")
    with pytest.raises(TransitionError, match="invalid completion receipt"):
        host.advance_stage("task-one", "run-one", Stage.RESEARCH, old, todo_ref=todo)


def test_receipt_with_unrelated_artifact_cannot_complete_stage(tmp_path: Path) -> None:
    host = HostController(tmp_path)
    host.init_task("task-one", "run-one")
    todo, _ = _completed_research_work(host, "task-one", "run-one")
    unrelated = _artifact(host, "unrelated-output", "not this work")
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id="task-one",
        run_id="run-one",
        artifact_id=unrelated.artifact_id,
        revision=1,
        artifact_digest=unrelated.artifact_digest,
    )
    with pytest.raises(TransitionError, match="evidence not in completed work"):
        host.advance_stage("task-one", "run-one", Stage.RESEARCH, receipt, todo_ref=todo)
    assert host.get_state("task-one").current_stage is Stage.RESEARCH


def test_forged_receipt_digest_fails(tmp_path: Path) -> None:
    host = HostController(tmp_path)
    host.init_task("task-one", "run-one")
    todo, evidence = _completed_research_work(host, "task-one", "run-one")
    receipt = host.issue_stage_receipt(
        Stage.RESEARCH,
        task_id="task-one",
        run_id="run-one",
        artifact_id=evidence.artifact_id,
        revision=1,
        artifact_digest=evidence.artifact_digest,
    )
    forged = ReceiptRef(receipt_id=receipt.receipt_id, receipt_digest="f" * 64, issuer_id="host")
    with pytest.raises(TransitionError, match="unverified host provenance"):
        host.advance_stage("task-one", "run-one", Stage.RESEARCH, forged, todo_ref=todo)
