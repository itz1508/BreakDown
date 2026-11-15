"""Audit skill executes migrated static checks without writing source files."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from system.host.skill_dispatch import AuditArguments, SkillContext
from agent.skills.auditor.audit import run


def test_auditor_preserves_file_bytes(tmp_path: Path) -> None:
    path = tmp_path / "hello.py"
    path.write_text("def hello():\n    return 1\n", encoding="utf-8")
    original = path.read_bytes()
    result = run(
        SkillContext(host=Mock(), workspace_root=tmp_path),
        Mock(information_needed="Inspect Python source"),
        AuditArguments(capabilities=("paths",)),
    )
    assert "paths" in result.executed_capabilities
    assert path.read_bytes() == original


def test_auditor_denies_scope_escape(tmp_path: Path) -> None:
    with pytest.raises((ValueError, OSError)):
        run(
            SkillContext(host=Mock(), workspace_root=tmp_path),
            Mock(information_needed="escape"),
            AuditArguments(scope="../"),
        )
