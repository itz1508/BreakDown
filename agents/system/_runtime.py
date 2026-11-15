"""Process runtime: one subprocess, three pipes, one timeout, no deadlocks."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

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
