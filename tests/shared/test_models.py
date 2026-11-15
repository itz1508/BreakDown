"""Shared model tests: identity, revisions, freezing and JSON round-trips."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from agents.shared.io import Request, error_response, ok_response
from system.storage import ExecStatus, TaskTodo, create_exec_todo, create_todo, finish_exec_todo


def test_create_todo_sets_identity_and_revision_one() -> None:
    todo = create_todo(skill="researcher", action="research", payload={"query": "x"})
    assert len(todo.todo_id) == 32
    assert todo.todo_revision == 1
    assert todo.skill == "researcher"
    assert todo.created_at.tzinfo is not None


def test_create_todo_rejects_non_serializable_payload() -> None:
    with pytest.raises(ValueError, match="JSON-serializable"):
        create_todo(skill="r", action="a", payload={"bad": object()})


def test_create_todo_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        create_todo(skill="r", action="a", payload=["not", "an", "object"])  # type: ignore[arg-type]


def test_todo_is_frozen() -> None:
    todo = create_todo(skill="r", action="a", payload={})
    with pytest.raises(ValidationError):
        todo.skill = "other"


def test_payload_deep_copy_isolates_caller() -> None:
    payload = {"nested": {"list": [1]}}
    todo = create_todo(skill="r", action="a", payload=payload)
    payload["nested"]["list"].append(2)
    assert todo.payload["nested"]["list"] == [1]


def test_todo_json_round_trip() -> None:
    todo = create_todo(skill="r", action="a", payload={"k": "v"})
    restored = TaskTodo.model_validate(json.loads(todo.model_dump_json()))
    assert restored == todo


def test_exec_todo_lifecycle() -> None:
    todo = create_todo(skill="r", action="a", payload={})
    record = create_exec_todo(todo)
    assert record.exec_revision == 1
    assert record.status is ExecStatus.RUNNING
    assert record.completed_at is None
    terminal = finish_exec_todo(record, ExecStatus.COMPLETED, 0, stdout_ref="output:x/stdout")
    assert terminal.exec_revision == 2
    assert terminal.status is ExecStatus.COMPLETED
    assert terminal.completed_at is not None
    assert terminal.stdout_ref == "output:x/stdout"


def test_exec_todo_rejects_double_finish_and_running_finish() -> None:
    todo = create_todo(skill="r", action="a", payload={})
    record = create_exec_todo(todo)
    with pytest.raises(ValueError, match="terminal status"):
        finish_exec_todo(record, ExecStatus.RUNNING, 0)
    terminal = finish_exec_todo(record, ExecStatus.FAILED, 1)
    with pytest.raises(ValueError, match="already terminal"):
        finish_exec_todo(terminal, ExecStatus.COMPLETED, 0)


def test_exec_todo_requires_matching_task_revision() -> None:
    todo = create_todo(skill="r", action="a", payload={})
    record = create_exec_todo(todo)
    assert record.todo_revision == todo.todo_revision == 1


def test_request_and_response_round_trip() -> None:
    request = Request(
        todo_id="t",
        todo_revision=1,
        exec_id="e",
        skill="auditor",
        action="discovery",
        payload={"scope": "."},
        workspace="w",
        state_root="s",
    )
    restored = Request.model_validate_json(request.model_dump_json())
    assert restored == request
    ok = ok_response({"answer": 1})
    assert json.loads(ok.model_dump_json())["ok"] is True
    err = error_response("boom", "went wrong")
    assert err.ok is False and err.error == {"code": "boom", "message": "went wrong"}
