"""CLI and module entrypoints consume the existing HostController Scanner."""

from __future__ import annotations

import json
from uuid import uuid4

from pydantic import BaseModel

from agent.cli import main
from agent.skills.planner.contracts.scanner import ScannerRunInput
from agent.skills.shared.contracts.workflow.system.host import ReceiptRef
from agent.skills.shared.host.sys_controller import HostController
from tests.planner.test_decision_trace import artifact_ref, make_planning_record


class _TaskInput(BaseModel):
    task_id: str
    text: str
    purpose: str = "research"


def prepared_scanner(tmp_path):
    host = HostController(str(tmp_path))
    task_id = uuid4().hex
    run_id = f"run-{task_id}"
    record = _TaskInput(task_id=task_id, text="Inspect exact Planning evidence")
    host.artifact_store.put_immutable(record, f"input:{task_id}", 1, "task_input", "1.0")
    host.init_task(task_id, run_id)
    checkpoint = host.checkpoint_store.load_checkpoint(task_id)
    assert checkpoint is not None
    revision, state, _ = checkpoint
    # Isolate the CLI adapter; the complete upstream Planning workflow is not supplied here.
    state["current_stage"] = "planning"
    host.checkpoint_store.checkpoint_cas(task_id, revision, state)
    planning = make_planning_record().model_copy(update={"task_id": task_id, "run_id": run_id})
    digest = host.artifact_store.put_immutable(planning, "candidate:" + task_id, 1, "planning", "1.0")
    request = ScannerRunInput(
        run_id=run_id,
        candidate_ref=artifact_ref("candidate:" + task_id, 1, digest),
        repository_identity="repo",
        capabilities=("dependency_readiness",),
        gap_result_ref=artifact_ref("missing-gap", 1, "c" * 64, "structural_analysis_result"),
        gap_receipt_ref=ReceiptRef(receipt_id="missing-receipt", receipt_digest="d" * 64, issuer_id="host"),
    )
    return host, task_id, request


def test_cli_scan_executes_the_host_scanner(tmp_path, monkeypatch, capsys):
    host, task_id, request = prepared_scanner(tmp_path)
    monkeypatch.setattr(HostController, "_verify_structural_gap", lambda *args: None)
    request_file = tmp_path / "scan-request.json"
    request_file.write_text(request.model_dump_json())
    monkeypatch.setattr(
        "sys.argv",
        ["agent", "scan", task_id, str(request_file), "--state-root", str(tmp_path)],
    )

    assert main() == 2
    output = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert output[0]["type"] == "scanner_started"
    assert output[-1]["type"] == "scanner_result"
    assert output[-1]["result"]["request_id"] == output[-2]["detail"]["scan_id"]
    assert host.event_store.list(task_id)[-1]["event_type"] == "scanner_completed"
