"""Regression coverage for exact canonical Agent role paths.

Legacy shim files are intentionally absent. Dispatch names are preserved
through narrowly scoped import-path changes, not a second runtime graph.
"""

from pathlib import Path

from system.host.skill_dispatch import registered_skills


ROOT = Path(__file__).resolve().parents[2]


def test_canonical_skill_file_names() -> None:
    for path in (
        "agent/skills/auditor/auditing.py",
        "agent/skills/researcher/researching.py",
        "agent/skills/coder/coding.py",
        "agent/skills/coder/code.yaml",
        "agent/skills/auditor/review/core.py",
        "agent/skills/planner/planning.py",
        "agent/skills/planner/review/gap_analysis.py",
        "contracts/workflow/pipeline.yaml",
    ):
        assert (ROOT / path).is_file(), path
    for obsolete in (
        "agent/skills/auditor/audit.py",
        "agent/skills/researcher/research.py",
        "agent/skills/researcher/search.yaml",
        "agent/skills/auditor/code_design.py",
        "agent/skills/code_design",
        "agent/skills/auditor/checks",
        "agent/skills/planner/plan.py",
        "agent/skills/planner/checks",
        "agent/breakdown.yaml",
    ):
        assert not (ROOT / obsolete).exists(), obsolete


def test_host_registered_paths_use_canonical_modules() -> None:
    registered = {
        (row["stage"], row["contract_role"]): row["module"]
        for row in registered_skills()
    }
    assert registered[("audit_discovery", "audit_discovery")] == "agent.skills.auditor.auditing"
    assert registered[("planning", "planner")] == "agent.skills.planner.planning"
