"""Working storage for temporary artifacts generated during runtime, scans, and active execution."""

from __future__ import annotations

import shutil
from pathlib import Path


class WorkingStorage:
    """Manages temporary execution artifacts (scratch files, scan dumps, working code buffers)."""

    def __init__(self, root: str | Path | None = None) -> None:
        if root is not None:
            self.root = Path(root)
        else:
            self.root = Path(".oneshot-state") / "working"
        self.root.mkdir(parents=True, exist_ok=True)

    def write_temp_artifact(self, relative_name: str, content: bytes | str) -> Path:
        target = (self.root / relative_name).resolve()
        if not target.is_relative_to(self.root.resolve()):
            raise ValueError(f"target path escapes working storage root: {relative_name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)
        return target

    def read_temp_artifact(self, relative_name: str) -> bytes:
        target = (self.root / relative_name).resolve()
        if not target.is_relative_to(self.root.resolve()):
            raise ValueError(f"target path escapes working storage root: {relative_name}")
        if not target.is_file():
            raise FileNotFoundError(f"temporary artifact not found: {relative_name}")
        return target.read_bytes()

    def clear(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)
            self.root.mkdir(parents=True, exist_ok=True)
