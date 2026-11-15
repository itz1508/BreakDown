"""Delegation: one ExecTodo, one subprocess, terminal state on every path."""

from __future__ import annotations

import asyncio
import json

from agents.shared.events.event import create_event
from agents.shared.io import Request
from agents.shared.queue.exec_todo import ExecStatus, ExecTodo, create_exec_todo, finish_exec_todo
from agents.shared.queue.task_todo import TaskTodo
from agents.system._call import call_ref
from agents.system._runtime import sys_runtime
from agents.system._storage import Storage

_TERMINAL_EVENTS = {
    "completed": "exec_completed",
    "failed": "exec_failed",
    "timed_out": "exec_timed_out",
    "cancelled": "exec_cancelled",
}


def _parse_response(stdout: str) -> dict | None:
    """Return the last JSON object in stdout, or None when the child produced none."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


async def delegating(
    todo: TaskTodo,
    storage: Storage,
    workspace: str,
    timeout_s: float = 30.0,
) -> ExecTodo:
    """Execute one todo immediately and persist a terminal ExecTodo on every path."""
    record = create_exec_todo(todo)
    storage.save_exec(record)
    storage.append_event(create_event("exec_started", todo.todo_id, record.exec_id))

    argv = call_ref(todo.skill, todo.action)
    request = Request(
        todo_id=todo.todo_id,
        todo_revision=todo.todo_revision,
        exec_id=record.exec_id,
        skill=todo.skill,
        action=todo.action,
        payload=todo.payload,
        workspace=workspace,
        state_root=str(storage.root),
    )
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    terminal: ExecTodo
    try:
        result = await sys_runtime(argv, request.model_dump(mode="json"), timeout_s=timeout_s)
        stdout_ref = storage.save_output(record.exec_id, "stdout", result.stdout)
        stderr_ref = storage.save_output(record.exec_id, "stderr", result.stderr)
        if result.timed_out:
            terminal = finish_exec_todo(record, ExecStatus.TIMED_OUT, result.exit_code, stdout_ref, stderr_ref)
        else:
            response = _parse_response(result.stdout)
            completed = result.exit_code == 0 and response is not None and response.get("ok") is True
            status = ExecStatus.COMPLETED if completed else ExecStatus.FAILED
            terminal = finish_exec_todo(record, status, result.exit_code, stdout_ref, stderr_ref)
    except asyncio.CancelledError:
        terminal = finish_exec_todo(record, ExecStatus.CANCELLED, None, stdout_ref, stderr_ref)
        storage.save_exec(terminal)
        storage.append_event(create_event(_TERMINAL_EVENTS["cancelled"], todo.todo_id, record.exec_id))
        raise

    storage.save_exec(terminal)
    storage.append_event(create_event(_TERMINAL_EVENTS[terminal.status.value], todo.todo_id, record.exec_id))
    return terminal
