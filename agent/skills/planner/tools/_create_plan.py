"""Create plan specification drafts from planning decisions.

Planner-owned: produces candidate plans for Host publication.
Does not publish, freeze, or template — those remain Host-owned.

Pattern: CPython ``Tools/freeze/freeze.py`` — an orchestrator that coordinates
sub-tools in sequence to produce a complete output.  This module calls
``_create_task_todo.create_task_todos`` to derive TaskTodo drafts from the
build specification, and optionally incorporates gap-analysis results into
the planning report, then assembles a ``CandidateSpecification`` draft.
"""

from __future__ import annotations

from typing import Any

from agent.skills.planner.types import BuildSpecification, CandidateSpecification


def create_plan(
    candidate_id: str,
    build_spec: BuildSpecification,
    *,
    planning_report: str = "",
    gap_result: Any | None = None,
) -> CandidateSpecification:
    """Create a candidate plan specification draft.

    Like CPython ``freeze.main``: orchestrate sub-tools in sequence.

    1.  Optionally incorporate *gap_result* into the planning report.
    2.  Delegate task-todo creation to ``_create_task_todo.create_task_todos``.
    3.  Assemble a ``CandidateSpecification`` draft for Host admission.

    No publication, no template creation — the Host's
    ``PlanTemplateService`` handles actual publication.
    """
    # Import here to avoid circular dependency at module level.
    from agent.skills.planner.tools._create_task_todo import create_task_todos

    # Step 1 — incorporate gap findings into the planning report.
    report_parts: list[str] = [planning_report] if planning_report else []
    if gap_result is not None:
        report_parts.append(_summarize_gap(gap_result))

    # Step 2 — create TaskTodo drafts (delegated, like freeze calls makefreeze).
    # The todos are returned for the caller's inspection; the Host decides
    # whether to freeze them into a Build.
    _todos = create_task_todos(build_spec)

    # Step 3 — assemble the candidate.
    return CandidateSpecification(
        candidate_id=candidate_id,
        specification_revision=1,
        build_spec=build_spec,
        planning_report="\n\n".join(report_parts),
    )


def _summarize_gap(gap_result: Any) -> str:
    """Render a brief gap-analysis summary for the planning report."""
    if hasattr(gap_result, "to_summary"):
        return gap_result.to_summary()
    if hasattr(gap_result, "to_dict"):
        import json
        return json.dumps(gap_result.to_dict(), sort_keys=True, indent=2)
    return str(gap_result)
