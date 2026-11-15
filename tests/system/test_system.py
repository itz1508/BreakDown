"""System tests: references, allow-list, storage and the process runtime."""

from __future__ import annotations

import json

import pytest

from agents.system import (
    UnknownSkillActionError,
    call_ref,
    coordinate,
    sys_ref,
    sys_runtime,
    sys_storage,
)
from system.storage import Storage, create_todo


def test_sys_ref_known_kinds_and_rejection() -> None:
    assert sys_ref("output", "e1/stdout") == "output:e1/stdout"
    with pytest.raises(ValueError, match="unknown reference kind"):
        sys_ref("banana", "x")
    with pytest.raises(ValueError, match="non-empty"):
        sys_ref("output", "")


def test_call_ref_returns_executable_module_argv() -> None:
    argv = call_ref("auditor", "discovery")
    assert argv[0].endswith("python.exe") or argv[0].endswith("python")
    assert argv[1] == "-m"
    assert argv[2] == "agents.skills.auditor"


def test_call_ref_rejects_unknown_pairs() -> None:
    with pytest.raises(UnknownSkillActionError):
        call_ref("researcher", "deploy")
    with pytest.raises(UnknownSkillActionError):
        call_ref("nobody", "nothing")


def test_storage_round_trip_and_revisions(tmp_path) -> None:
    storage = sys_storage(tmp_path)
    todo = create_todo(skill="auditor", action="discovery", payload={"scope": "."})
    assert storage.save_todo(todo) == 1
    latest = storage.get_todo(todo.todo_id)
    assert latest is not None and latest.skill == "auditor"
    assert storage.get_todo("missing") is None


def test_storage_events_are_append_ordered(tmp_path) -> None:
    from system.storage import create_event

    storage = sys_storage(tmp_path)
    todo = create_todo(skill="auditor", action="discovery", payload={})
    storage.append_event(create_event("todo_created", todo.todo_id))
    storage.append_event(create_event("exec_started", todo.todo_id, "e1"))
    events = storage.list_events(todo.todo_id)
    assert [e.event_type for e in events] == ["todo_created", "exec_started"]
    with pytest.raises(ValueError, match="requires an exec_id"):
        create_event("exec_started", todo.todo_id)


def test_sys_runtime_stdin_stdout_round_trip(tmp_path) -> None:
    import asyncio

    argv = ("python", "-c", "import sys,json; d=json.load(sys.stdin); print(json.dumps({'seen': d['hello']}))")
    result = asyncio.run(sys_runtime(argv, {"hello": "world"}, timeout_s=15))
    assert result.exit_code == 0
    assert not result.timed_out
    assert json.loads(result.stdout)["seen"] == "world"


def test_sys_runtime_reports_stderr_and_nonzero_exit(tmp_path) -> None:
    import asyncio

    argv = ("python", "-c", "import sys; sys.stderr.write('bad input'); raise SystemExit(3)")
    result = asyncio.run(sys_runtime(argv, {}, timeout_s=15))
    assert result.exit_code == 3
    assert "bad input" in result.stderr


def test_sys_runtime_enforces_timeout(tmp_path) -> None:
    import asyncio

    argv = ("python", "-c", "import time; time.sleep(30)")
    result = asyncio.run(sys_runtime(argv, {}, timeout_s=2))
    assert result.timed_out
    assert result.completed_at > result.started_at


def test_storage_output_refs_round_trip(tmp_path) -> None:
    from agents.system import sys_ref

    storage = Storage(tmp_path)
    ref = storage.save_output("e1", "stdout", "captured output")
    assert ref == sys_ref("output", "e1/stdout")
    assert storage.read_output(ref) == "captured output"
    with pytest.raises(ValueError, match="invalid output reference"):
        storage.read_output(sys_ref("output", "../escape"))


def test_coordinate_runs_the_auditor_end_to_end(tmp_path) -> None:
    import asyncio

    (tmp_path / "workspace").mkdir()
    (tmp_path / "workspace" / "hello.py").write_text("TOKEN = 'ready'\n", encoding="utf-8")
    storage = Storage(tmp_path / "state")
    todo = create_todo(
        skill="auditor",
        action="discovery",
        payload={"request": "audit broken imports", "scope": ".", "capabilities": ["paths"]},
    )
    terminal = asyncio.run(coordinate(todo, storage, str(tmp_path / "workspace"), timeout_s=60))
    assert terminal.status.value in {"completed", "failed"}
    events = [e.event_type for e in storage.list_events(todo.todo_id)]
    assert events[0] == "todo_created"
    assert events[-1] in {"exec_completed", "exec_failed"}
    saved = storage.get_todo(todo.todo_id)
    assert saved is not None
    record = storage.get_exec_todo(terminal.exec_id)
    assert record is not None and record.attempt_no == 1
