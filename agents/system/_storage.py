"""File-backed storage: todos, exec revisions, events and process output.

No database is introduced. Every save is an append: a new numbered file per
revision, one JSONL file per todo's event log, one text file per captured
output stream. Reading a todo or exec returns the highest revision.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.shared.events.event import Event
from agents.shared.queue.exec_todo import ExecTodo
from agents.shared.queue.task_todo import TaskTodo
from agents.system._ref import sys_ref

_DEFAULT_ROOT = ".oneshot-state"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


class Storage:
    """File-backed append-only storage. ``root`` is the state root."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else Path(_DEFAULT_ROOT)

    # -- todos ------------------------------------------------------------
    def save_todo(self, todo: TaskTodo) -> int:
        directory = self.root / "todos" / todo.todo_id
        revision = self._next_revision(directory)
        _write_json(directory / f"rev-{revision}.json", todo.model_dump(mode="json"))
        return revision

    def get_todo(self, todo_id: str) -> TaskTodo | None:
        directory = self.root / "todos" / todo_id
        latest = self._latest_revision(directory)
        if latest is None:
            return None
        return TaskTodo.model_validate(_read_json(directory / f"rev-{latest}.json"))

    # -- exec todos -------------------------------------------------------
    def save_exec(self, record: ExecTodo) -> int:
        directory = self.root / "execs" / record.exec_id
        revision = self._next_revision(directory)
        _write_json(directory / f"rev-{revision}.json", record.model_dump(mode="json"))
        return revision

    def get_exec_todo(self, exec_id: str) -> ExecTodo | None:
        directory = self.root / "execs" / exec_id
        latest = self._latest_revision(directory)
        if latest is None:
            return None
        return ExecTodo.model_validate(_read_json(directory / f"rev-{latest}.json"))

    def list_execs(self, todo_id: str) -> tuple[ExecTodo, ...]:
        execs_dir = self.root / "execs"
        if not execs_dir.is_dir():
            return ()
        records = []
        for exec_dir in sorted(execs_dir.iterdir()):
            latest = self._latest_revision(exec_dir)
            if latest is None:
                continue
            record = ExecTodo.model_validate(_read_json(exec_dir / f"rev-{latest}.json"))
            if record.todo_id == todo_id:
                records.append(record)
        return tuple(records)

    # -- events -----------------------------------------------------------
    def append_event(self, event: Event) -> None:
        log = self.root / "events" / f"{event.todo_id}.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def list_events(self, todo_id: str) -> tuple[Event, ...]:
        log = self.root / "events" / f"{todo_id}.jsonl"
        if not log.is_file():
            return ()
        events = []
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(Event.model_validate(json.loads(line)))
        return tuple(events)

    # -- process output ---------------------------------------------------
    def save_output(self, exec_id: str, stream_name: str, content: str) -> str:
        path = self.root / "outputs" / f"{exec_id}-{stream_name}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return sys_ref("output", f"{exec_id}/{stream_name}")

    def read_output(self, ref: str) -> str:
        ident = ref.removeprefix("output:")
        relative = ident.split("/", 1)
        if len(relative) != 2 or "/" in relative[1] or ".." in relative:
            raise ValueError(f"invalid output reference: {ref!r}")
        path = self.root / "outputs" / f"{relative[0]}-{relative[1]}.txt"
        return path.read_text(encoding="utf-8", errors="replace")

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _next_revision(directory: Path) -> int:
        if not directory.is_dir():
            return 1
        revisions = [int(p.stem.split("-")[1]) for p in directory.glob("rev-*.json")]
        return max(revisions, default=0) + 1

    @staticmethod
    def _latest_revision(directory: Path) -> int | None:
        if not directory.is_dir():
            return None
        revisions = [int(p.stem.split("-")[1]) for p in directory.glob("rev-*.json")]
        return max(revisions) if revisions else None


def sys_storage(root: str | Path | None = None) -> Storage:
    """Return the file-backed storage rooted at ``root`` (default state root)."""
    return Storage(root)
