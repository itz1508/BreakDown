"""Shared Planning coverage result shape, independent of validation module imports."""

from __future__ import annotations

from agents.shared.base import ContractModel
from agents.skills.planner.contracts.specification import IssueType


class PlanningCoverage(ContractModel):
    """Sources for every category, including categories left uncovered."""

    category_sources: dict[IssueType, tuple[str, ...]]
    uncovered_categories: tuple[IssueType, ...] = ()
    unmapped_scanner_capabilities: tuple[str, ...] = ()
