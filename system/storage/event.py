"""Events: an append-only log of what happened to one todo."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

EVENT_TYPES = (
    "todo_created",
    "exec_started",
    "exec_completed",
    "exec_failed",
    "exec_timed_out",
    "exec_cancelled",
)


class Event(BaseModel):
    """One appended fact. Order is storage append order, never timestamp order."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    todo_id: str = Field(min_length=1)
    exec_id: str | None = None
    timestamp: datetime
    data: dict[str, Any] = Field(default_factory=dict)


def create_event(
    event_type: str,
    todo_id: str,
    exec_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> Event:
    """Build one event; the event type must be one of the known types."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown event type: {event_type!r}")
    if event_type != "todo_created" and not exec_id:
        raise ValueError(f"event type {event_type!r} requires an exec_id")
    return Event(
        event_id=uuid.uuid4().hex,
        event_type=event_type,
        todo_id=todo_id,
        exec_id=exec_id,
        timestamp=datetime.now(UTC),
        data=dict(data or {}),
    )
