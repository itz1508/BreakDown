"""Create TaskTodo drafts from BuildSpecification inputs.

Planner-owned: produces candidate task todos for Host admission.
Does not authorize, freeze, dispatch, or verify — those remain Host-owned.

Pattern: CPython ``Tools/freeze/makefreeze.py`` — iterate sorted input items,
produce structured output per item.  Each BuildAction becomes one TaskTodo
draft with authorized paths, expected preimages, and instructions drawn from
the action's validation steps and verification tools.
"""

from __future__ import annotations

from agent.skills.planner.types import BuildAction, BuildSpecification, TaskTodo


def _action_paths(action: BuildAction) -> tuple[str, ...]:
    """Return the filesystem paths a build action is authorized to touch."""
    paths: list[str] = []
    if hasattr(action, "source_path"):
        paths.append(action.source_path)
    if hasattr(action, "target_path") and action.target_path not in paths:
        paths.append(action.target_path)
    return tuple(paths)


def _action_preimages(action: BuildAction) -> dict[str, str | None]:
    """Build expected-preimage dict keyed exactly to *action* paths.

    CreateAction has no source digest (target is new); others carry
    ``expected_source_digest`` for the source path.
    """
    preimages: dict[str, str | None] = {}
    source_digest = getattr(action, "expected_source_digest", None)
    for path in _action_paths(action):
        preimages[path] = source_digest if path == getattr(action, "source_path", None) else None
    return preimages


def create_task_todos(
    specification: BuildSpecification,
    *,
    findings: tuple[str, ...] = (),
) -> tuple[TaskTodo, ...]:
    """Create TaskTodo drafts from BuildSpecification actions.

    Like CPython ``makefreeze``: iterate sorted input items, produce
    structured output per item.  Each action becomes a TaskTodo draft with
    authorized paths, expected preimages, and instructions.

    No persistence, no Host dispatch — produces drafts only.
    """
    actions = sorted(specification.actions, key=lambda a: a.action_id)
    todos: list[TaskTodo] = []

    for action in actions:
        authorized = _action_paths(action)
        if not authorized:
            continue

        todo = TaskTodo(
            todo_id=f"todo:{action.action_id}",
            todo_revision=1,
            title=f"Build action {action.action_id}",
            objective=specification.objective,
            source_action_ids=(action.action_id,),
            dependency_todo_ids=tuple(f"todo:{dep}" for dep in action.depends_on),
            authorized_paths=authorized,
            expected_preimages=_action_preimages(action),
            instructions=action.validation_steps,
            verification=action.verification_tools,
            expected_result=action.expected_result,
            recovery_requirements=(action.recovery_requirement,),
        )
        todos.append(todo)

    return tuple(todos)