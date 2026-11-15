"""Queue storage: the durable home for requested work, attempts and events.

The queue requires storage and persists here (user ruling) — never in
agents/. Models (TaskTodo, ExecTodo, Event), the reference format and the
file-backed append-only store all live in this package.
"""

from __future__ import annotations

from system.storage._ref import sys_ref
from system.storage.event import EVENT_TYPES, Event, create_event
from system.storage.exec_todo import ExecStatus, ExecTodo, create_exec_todo, finish_exec_todo
from system.storage.queue import Storage, sys_storage
from system.storage.task_todo import TaskTodo, create_todo

__all__ = [
    "EVENT_TYPES",
    "Event",
    "ExecStatus",
    "ExecTodo",
    "Storage",
    "TaskTodo",
    "create_event",
    "create_exec_todo",
    "create_todo",
    "finish_exec_todo",
    "sys_ref",
    "sys_storage",
]
