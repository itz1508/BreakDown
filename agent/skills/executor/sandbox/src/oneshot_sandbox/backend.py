"""Provider-neutral Sandbox backend interface; no provider SDK or permissions."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .contracts import SandboxExecutionRequest


class SandboxHandle(Protocol):
    object_id: str

    def poll(self) -> Any: ...


class SandboxBackend(Protocol):
    def create(self, request: SandboxExecutionRequest, name: str) -> SandboxHandle: ...

    def upload(self, sandbox: SandboxHandle, request: SandboxExecutionRequest) -> None: ...

    def execute(self, sandbox: SandboxHandle, timeout_seconds: int) -> int: ...

    def download(self, sandbox: SandboxHandle, target: Path) -> tuple[Path, Path, Path]: ...

    def terminate(self, sandbox: SandboxHandle) -> None: ...

    def recover(self, sandbox_name: str, sandbox_id: str | None) -> SandboxHandle: ...
