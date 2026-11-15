"""ExecTodo: one execution attempt against one exact TaskTodo revision."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agents.shared.queue.task_todo import TaskTodo


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ExecStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class ExecTodo(BaseModel):
    """One attempt's record. Never mutated: every save is a new revision."""

    model_config = ConfigDict(frozen=True)

    exec_id: str = Field(min_length=1)
    todo_id: str = Field(min_length=1)
    todo_revision: int = Field(ge=1)
    attempt_no: int = Field(ge=1)
    exec_revision: int = Field(ge=1)
    started_at: datetime
    completed_at: datetime | None = None
    status: ExecStatus
    exit_code: int | None = None
    stdout_ref: str | None = None
    stderr_ref: str | None = None


def create_exec_todo(
    task: TaskTodo,
    attempt_no: int = 1,
    *,
    status: Literal[ExecStatus.RUNNING] = ExecStatus.RUNNING,
) -> ExecTodo:
    """Create revision 1 of an ExecTodo bound to the task's exact revision."""
    return ExecTodo(
        exec_id=uuid.uuid4().hex,
        todo_id=task.todo_id,
        todo_revision=task.todo_revision,
        attempt_no=attempt_no,
        exec_revision=1,
        started_at=_utcnow(),
        status=status,
    )


def finish_exec_todo(
    record: ExecTodo,
    status: ExecStatus,
    exit_code: int | None,
    stdout_ref: str | None = None,
    stderr_ref: str | None = None,
) -> ExecTodo:
    """Return the next revision of the record in a terminal state."""
    if record.status is not ExecStatus.RUNNING:
        raise ValueError(f"exec {record.exec_id} is already terminal ({record.status})")
    if status is ExecStatus.RUNNING:
        raise ValueError("finish_exec_todo requires a terminal status")
    return record.model_copy(
        update={
            "exec_revision": record.exec_revision + 1,
            "completed_at": _utcnow(),
            "status": status,
            "exit_code": exit_code,
            "stdout_ref": stdout_ref,
            "stderr_ref": stderr_ref,
        }
    )
