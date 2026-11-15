"""Research role reuses the actual host service and rejects mixed roots."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from system.host.skill_dispatch import ResearchArguments, SkillContext
from agent.skills.researcher.research import run


def test_researcher_rejects_different_state_roots(tmp_path: Path) -> None:
    service = Mock()
    service.host.state_root = tmp_path / "other"
    with pytest.raises(ValueError, match="different state roots"):
        run(SkillContext(host=Mock(state_root=tmp_path), workspace_root=tmp_path,
                         research_service=service), Mock(task_id="task"), ResearchArguments())


def test_researcher_invokes_existing_host_service(tmp_path: Path) -> None:
    service = Mock()
    service.host.state_root = tmp_path
    context = SkillContext(host=Mock(state_root=tmp_path), workspace_root=tmp_path, research_service=service)
    with patch("mvp.research_host.execute_research", return_value={"status": "delegated"}) as execute:
        assert run(context, Mock(task_id="task"), ResearchArguments()) == {"status": "delegated"}
    execute.assert_called_once_with(service, "task")
