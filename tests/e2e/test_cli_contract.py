"""CLI contract: documented commands run against real host state.

The CLI is the only supported operator surface, so these tests invoke it the way
an operator or CI does: a real subprocess for `skills`, and the real command
functions for state that lives in a disposable state root.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from agent.cli import cmd_resume, cmd_status, cmd_verify, main
from agent.skills.planner.contracts.scanner import ScannerRunInput
from agent.skills.shared.contracts.workflow.system.host import ReceiptRef
from agent.skills.shared.host.sys_controller import HostController
from tests.e2e.harness import create_task, prepare_planning_candidate
from tests.fixtures.planning import artifact_ref

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.e2e


def test_skills_command_lists_registered_roles() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "agent", "skills"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    skills = json.loads(completed.stdout)
    assert sorted(item["stage"] for item in skills) == [
        "candidate_completion",
        "discovery",
        "gap_inspection",
        "planning",
        "repository_reconciliation",
        "research",
        "sandbox_execution",
    ]
    assert {item["module"] for item in skills} == {
        "agent.skills.auditor.auditing",
        "agent.skills.builder.building",
        "agent.skills.coder.coding",
        "agent.skills.planner.planning",
        "agent.skills.researcher.researching",
    }


def test_status_resume_and_verify_report_host_state(tmp_path, capsys) -> None:
    HostController(tmp_path).init_task("cli-task", "cli-run")

    assert cmd_status("cli-task", str(tmp_path)) == 0
    state = json.loads(capsys.readouterr().out)
    assert state["task_id"] == "cli-task"
    assert state["current_stage"] == "user_request"

    assert cmd_resume("cli-task", str(tmp_path)) == 0
    assert "user_request" in capsys.readouterr().out

    assert cmd_verify("cli-task", str(tmp_path)) == 1
    assert "in progress" in capsys.readouterr().out

    assert cmd_status("missing-task", str(tmp_path)) == 1


def test_cli_scan_executes_the_host_scanner(tmp_path, monkeypatch, capsys) -> None:
    host = HostController(str(tmp_path))
    task_id = uuid4().hex
    run_id = f"run-{task_id}"
    create_task(host, task_id, run_id, "Inspect exact Planning evidence")
    candidate_ref = prepare_planning_candidate(host, task_id, run_id)
    request = ScannerRunInput(
        run_id=run_id,
        candidate_ref=candidate_ref,
        repository_identity="repo",
        capabilities=("dependency_readiness",),
        gap_result_ref=artifact_ref("missing-gap", 1, "c" * 64, "structural_analysis_result"),
        gap_receipt_ref=ReceiptRef(receipt_id="missing-receipt", receipt_digest="d" * 64, issuer_id="host"),
    )
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

    assert cmd_verify("missing-task", str(tmp_path)) == 1
