"""Host dispatch blocks role substitution before any skill module is loaded."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agent.runtime.controller import TransitionError
from agent.runtime.skill_dispatch import AuditArguments, SkillContext, execute_skill, registered_skills


def test_four_registered_roles() -> None:
    items = registered_skills()
    assert len(items) == 4
    assert {item["contract_role"] for item in items} == {
        "audit_discovery", "researcher", "planner", "builder",
    }
    assert len({item["stage"] for item in items}) == 4


def test_wrong_role_cannot_import(tmp_path: Path) -> None:
    host = Mock()
    envelope = Mock(stage="build", role="researcher")
    context = SkillContext(host=host, workspace_root=tmp_path)
    with patch("agent.runtime.skill_dispatch.import_module") as imported:
        with pytest.raises(TransitionError, match="no executable skill"):
            execute_skill(context, envelope, AuditArguments())
    host.verify_agent_dispatch.assert_called_once_with(envelope)
    imported.assert_not_called()


def test_wrong_args_cannot_import(tmp_path: Path) -> None:
    host = Mock()
    envelope = Mock(stage="build", role="builder")
    with patch("agent.runtime.skill_dispatch.import_module") as imported:
        with pytest.raises(TransitionError, match="argument type"):
            execute_skill(SkillContext(host=host, workspace_root=tmp_path), envelope, AuditArguments())
    imported.assert_not_called()


def test_failed_host_receipt_check_blocks_dispatch(tmp_path: Path) -> None:
    host = Mock()
    host.verify_agent_dispatch.side_effect = TransitionError("stale dispatch")
    with patch("agent.runtime.skill_dispatch.import_module") as imported:
        with pytest.raises(TransitionError, match="stale dispatch"):
            execute_skill(
                SkillContext(host=host, workspace_root=tmp_path),
                Mock(stage="audit_discovery", role="audit_discovery"),
                AuditArguments(),
            )
    imported.assert_not_called()
