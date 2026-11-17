"""Process runtime: one subprocess, three pipes, one timeout, no deadlocks."""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_TERMINATE_GRACE_SECONDS = 5.0


@dataclass(frozen=True)
class RuntimeResult:
    """What one child process actually did."""

    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    started_at: datetime
    completed_at: datetime


async def sys_runtime(
    argv: tuple[str, ...],
    stdin_payload: dict[str, Any],
    timeout_s: float = 30.0,
) -> RuntimeResult:
    """Run argv once: write the JSON payload to stdin, drain both pipes, enforce the timeout.

    ``communicate()`` feeds stdin and drains stdout and stderr concurrently, so a
    chatty child can never fill a pipe buffer and deadlock the parent. On timeout
    the child is terminated and, after a grace period, killed; the partial output
    collected so far is returned with ``timed_out=True``.
    """
    if not argv or not argv[0]:
        raise ValueError("argv must start with an executable")
    started_at = datetime.now(UTC)
    process = await asyncio.create_subprocess_exec(
        argv[0],
        *argv[1:],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdin_data = json.dumps(stdin_payload).encode("utf-8")
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(stdin_data), timeout=timeout_s)
    except TimeoutError:
        return await _terminate_and_collect(process, started_at)
    except asyncio.CancelledError:
        await _terminate_and_collect(process, started_at)
        raise
    return RuntimeResult(
        exit_code=process.returncode,
        stdout=stdout.decode("utf-8", "replace"),
        stderr=stderr.decode("utf-8", "replace"),
        timed_out=False,
        started_at=started_at,
        completed_at=datetime.now(UTC),
    )


async def _terminate_and_collect(process: asyncio.subprocess.Process, started_at: datetime) -> RuntimeResult:
    """Terminate the child, then kill after a grace period, then collect what we can."""
    process.terminate()
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=_TERMINATE_GRACE_SECONDS)
    except TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
    return RuntimeResult(
        exit_code=process.returncode,
        stdout=stdout.decode("utf-8", "replace"),
        stderr=stderr.decode("utf-8", "replace"),
        timed_out=True,
        started_at=started_at,
        completed_at=datetime.now(UTC),
    )


# Stdin/stdout JSON envelope for skill processes (folded from the retired
# agents/shared/io.py). One request is read from stdin as a single JSON
# document; exactly one JSON response is written to stdout. Diagnostics go to
# stderr. Exit codes carry success: a non-zero exit means the response
# reported failure or the process crashed before responding.


class Request(BaseModel):
    """One work request, composed by the delegating layer and read from stdin."""

    model_config = ConfigDict(frozen=True)

    todo_id: str = Field(min_length=1)
    todo_revision: int = Field(ge=1)
    exec_id: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    action: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    workspace: str = Field(min_length=1)
    state_root: str = Field(min_length=1)


class Response(BaseModel):
    """Exactly one response document; ``ok`` false carries a typed error."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None


def read_request(stream: Any = None) -> Request:
    """Read and validate one request document from stdin."""
    raw = (sys.stdin if stream is None else stream).read()
    data = json.loads(raw)
    return Request.model_validate(data)


def write_response(response: Response, stream: Any = None) -> None:
    """Write exactly one JSON response document followed by a newline."""
    out = sys.stdout if stream is None else stream
    out.write(json.dumps(response.model_dump(mode="json")))
    out.write("\n")
    out.flush()


def ok_response(result: dict[str, Any] | None = None) -> Response:
    return Response(ok=True, result=result or {})


def error_response(code: str, message: str) -> Response:
    return Response(ok=False, error={"code": code, "message": message})
