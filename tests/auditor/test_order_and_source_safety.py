"""Auditor order, source containment, and CodeDesign handoff regressions."""

from pathlib import Path

import pytest

from agent.skills.auditor.review.core import CAPABILITY_ORDER, safe_read_text, scan


def test_canonical_order_and_selected_subset(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_smoke.py").write_text("def test_smoke(): assert True\n", encoding="utf-8")
    assert CAPABILITY_ORDER == (
        "paths",
        "contracts",
        "dependencies",
        "security",
        "completeness",
        "wiring",
        "frontend",
        "integration",
        "state",
        "recovery",
        "verification",
    )
    selected = ("verification", "security", "paths", "security", "contracts")
    result = scan(tmp_path, capabilities=selected)
    assert result.requested_capabilities == ("verification", "security", "paths", "contracts")
    assert result.executed_capabilities == ("paths", "contracts", "security", "verification")
    assert result.disposition == "not_e2e_verified"


def test_absolute_scope_rejected_even_when_inside_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="relative"):
        scan(tmp_path, scope=str(tmp_path), capabilities=("paths",))


def test_in_root_regular_source_is_readable(tmp_path: Path) -> None:
    p = tmp_path / "safe.py"
    p.write_text("x = 1\n", encoding="utf-8")
    assert safe_read_text(tmp_path, p) == "x = 1\n"


def test_symlink_source_blocked_and_other_findings_retained(tmp_path: Path) -> None:
    outside = tmp_path.parent / (tmp_path.name + "-external.py")
    outside.write_text("outside_marker = 3\n", encoding="utf-8")
    web = tmp_path / "web" / "src"
    mvp = tmp_path / "mvp"
    web.mkdir(parents=True)
    mvp.mkdir()
    (web / "main.jsx").write_text("fetch('/api/unknown')\n", encoding="utf-8")
    (mvp / "api.py").symlink_to(outside)
    result = scan(tmp_path, capabilities=("wiring", "paths"))
    assert result.disposition == "blocked"
    assert result.executed_capabilities == ("paths",)
    assert any(f.code == "PATH_OUTSIDE_REPOSITORY" for f in result.findings)
    assert any("wiring not completed" in reason for reason in result.limitations)
    assert outside.read_text(encoding="utf-8") == "outside_marker = 3\n"


def test_symlink_inside_root_is_not_read_as_audited_source(tmp_path: Path) -> None:
    real = tmp_path / "real.py"
    real.write_text("x = 1\n", encoding="utf-8")
    alias = tmp_path / "alias.py"
    alias.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        safe_read_text(tmp_path, alias)
