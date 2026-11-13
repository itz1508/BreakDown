"""Pin the reconciled five-skill layout and shared verification tool ownership."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_skill_file_names() -> None:
    for path in (
        "agent/skills/auditor/auditing.py",
        "agent/skills/auditor/audit.yaml",
        "agent/skills/auditor/review/core.py",
        "agent/skills/builder/building.py",
        "agent/skills/builder/build.yaml",
        "agent/skills/coder/coding.py",
        "agent/skills/coder/code.yaml",
        "agent/skills/planner/planning.py",
        "agent/skills/planner/plan.yaml",
        "agent/skills/planner/fixtures.py",
        "agent/skills/planner/review/gap_analysis.py",
        "agent/skills/researcher/researching.py",
        "agent/skills/researcher/research.yaml",
        "agent/skills/tools/verify_all.py",
        "agent/skills/tools/sys_scan.py",
        "agent/skills/shared/contracts/workflow/verifier/fixture_validation.py",
        "agent/skills/shared/host/file_operations.py",
        "agent/skills/shared/host/traceback_report.py",
    ):
        assert (ROOT / path).is_file(), path


def test_obsolete_skill_paths_are_absent() -> None:
    for obsolete in (
        "agent/skills/auditor/code_design.py",
        "agent/skills/auditor/checks",
        "agent/skills/auditor/tools",
        "agent/skills/planner/checks",
        "agent/skills/planner/tools",
        "agent/skills/planner/plan.py",
        "agent/skills/fixturer",
        "agent/skills/code_design",
        "agent/skills/executor",
        "contracts",
        "system",
    ):
        assert not (ROOT / obsolete).exists(), obsolete


def test_verification_is_shared_tool_not_a_skill() -> None:
    """verify_all compares Scanner observations only; it owns no skill folder."""
    source = (ROOT / "agent/skills/tools/verify_all.py").read_text(encoding="utf-8")
    assert "does not certify receipts" in source or "substitute for independent Build E2E" in source
    assert not (ROOT / "agent/skills/verifier").exists()
