"""Breakdown skill-based architecture — role-scoped capability packages.

Each skill exposes a consistent ``run.py`` interface (PRE/POST dispatch)
and declares its tools, checks, inputs, outputs, and Runtime integration
requirements in ``SKILL.md``.

Skills are read-only observers and planners. They never issue trusted
receipts or authorize their own operations. The Runtime (``agent.runtime``)
remains the single authority for authorization, persistence, stage
transitions, and execution gates.
"""

__all__ = ["auditor", "builder", "planner", "researcher"]
