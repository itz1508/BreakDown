"""Audit role runs read-only through host dispatch and refuses scope escape.

Both properties are enforced against the real HostController, a persisted dispatch
envelope and the real filesystem scanner, so a regression cannot hide behind a
stubbed collaborator.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import pytest

from agents.skills.auditor.auditing import run
from agents.skills.auditor.tools.core import AuditResult
from agents.skills.shared.contracts.workflow.system.host import HostDispatchEnvelope
from agents.skills.shared.host.skill_dispatch import AuditArguments, SkillContext, execute_skill
from agents.skills.shared.host.sys_controller import HostController
from tests.e2e.harness import advance, create_task

pytestmark = pytest.mark.e2e

TASK_ID = "task-audit"
RUN_ID = "run-audit"
SOURCE = "def hello():\n    return 1\n"


class DispatchedAudit(NamedTuple):
    host: HostController
    workspace: Path
    context: SkillContext
    envelope: HostDispatchEnvelope


def dispatched_audit(tmp_path: Path) -> DispatchedAudit:
    """Create a task, reach the discovery stage, and allocate the host dispatch route."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "hello.py").write_text(SOURCE, encoding="utf-8")
    host = HostController(tmp_path / "state", workspace)
    input_ref = create_task(host, TASK_ID, RUN_ID)
    # The host only allocates the audit route while discovery is the active stage.
    from agents.skills.shared.host.sys_controller import STAGE_ORDER

    for stage in STAGE_ORDER[:3]:
        advance(host, TASK_ID, RUN_ID, stage)
    envelope, _, _ = host.prepare_agent_dispatch(TASK_ID, input_ref, "Inspect Python source", requested_role="auditor")
    return DispatchedAudit(host, workspace, SkillContext.from_host(host, workspace), envelope)


def test_audit_skill_returns_findings_without_writing_source(tmp_path) -> None:
    dispatched = dispatched_audit(tmp_path)
    before = (dispatched.workspace / "hello.py").read_bytes()

    result = execute_skill(dispatched.context, dispatched.envelope, AuditArguments(capabilities=("paths",)))

    assert isinstance(result, AuditResult)
    assert "paths" in result.executed_capabilities
    assert (dispatched.workspace / "hello.py").read_bytes() == before
    events = [event["event_type"] for event in dispatched.host.event_store.list(TASK_ID)]
    assert events[-2:] == ["skill_started", "skill_finished"]


def test_audit_scope_escape_is_refused(tmp_path) -> None:
    dispatched = dispatched_audit(tmp_path)
    with pytest.raises(ValueError, match="escapes repository root"):
        run(dispatched.context, dispatched.envelope, AuditArguments(scope="../"))
