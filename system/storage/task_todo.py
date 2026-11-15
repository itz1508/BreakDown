"""TaskTodo: requested work only — no status, no scheduling, no process data."""

from __future__ import annotations

import copy
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TaskTodo(BaseModel):
    """One unit of requested work, identified by id and revision.

    The model is frozen; a change is a new revision, never a mutation. The
    payload is stored as plain JSON-serializable data and deep-copied on
    creation. Note: freezing the model does not deep-freeze nested mutable
    objects inside ``payload`` — callers must treat payload contents as
    immutable by convention.
    """

    model_config = ConfigDict(frozen=True)

    todo_id: str = Field(min_length=1)
    todo_revision: int = Field(ge=1)
    skill: str = Field(min_length=1)
    action: str = Field(min_length=1)
    payload: dict[str, Any]
    created_at: datetime

    @field_validator("payload")
    @classmethod
    def _payload_must_be_json_serializable(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            json.dumps(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"payload must be JSON-serializable: {exc}") from exc
        return value


def create_todo(skill: str, action: str, payload: dict[str, Any]) -> TaskTodo:
    """Create revision 1 of a TaskTodo with a fresh identity."""
    if not skill or not isinstance(skill, str):
        raise ValueError("skill must be a non-empty string")
    if not action or not isinstance(action, str):
        raise ValueError("action must be a non-empty string")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return TaskTodo(
        todo_id=uuid.uuid4().hex,
        todo_revision=1,
        skill=skill,
        action=action,
        payload=copy.deepcopy(payload),
        created_at=_utcnow(),
    )
