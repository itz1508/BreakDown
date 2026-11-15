"""Coordination: save the requested work, process it immediately, return the record."""

from __future__ import annotations

from agents.system._delegating import delegating
from system.storage import ExecTodo, Storage, TaskTodo, create_event


async def coordinate(
    todo: TaskTodo,
    storage: Storage,
    workspace: str,
    timeout_s: float = 30.0,
) -> ExecTodo:
    """Save the todo, record its creation, and delegate it immediately.

    There is no scheduler, batching, wave management or polling here: one call
    processes one todo and returns its terminal execution record.
    """
    storage.save_todo(todo)
    storage.append_event(create_event("todo_created", todo.todo_id))
    return await delegating(todo, storage, workspace, timeout_s=timeout_s)
