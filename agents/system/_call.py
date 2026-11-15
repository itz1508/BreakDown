"""Resolve an approved (skill, action) pair to a fixed subprocess argv."""

from __future__ import annotations

import sys

_SKILL_MODULES: dict[tuple[str, str], str] = {
    ("researcher", "research"): "agents.skills.researcher",
    ("auditor", "discovery"): "agents.skills.auditor",
    ("auditor", "repository_reconciliation"): "agents.skills.auditor",
    ("auditor", "gap_inspection"): "agents.skills.auditor",
    ("planner", "planning"): "agents.skills.planner",
    ("coder", "candidate_completion"): "agents.skills.coder",
    ("builder", "sandbox_execution"): "agents.skills.builder",
}


class UnknownSkillActionError(LookupError):
    """The (skill, action) pair is not in the approved allow-list."""


def call_ref(skill: str, action: str) -> tuple[str, ...]:
    """Return the argv for an approved pair; unknown pairs fail closed."""
    module = _SKILL_MODULES.get((skill, action))
    if module is None:
        raise UnknownSkillActionError(f"no approved action {action!r} for skill {skill!r}")
    return (sys.executable, "-m", module)
