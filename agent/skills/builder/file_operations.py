"""Physical file operations used only after the Host has admitted the action.

These functions do not approve changes, validate receipts, check path policy,
or issue recovery evidence. Those responsibilities remain with the Host.
Use Python's standard-library filesystem primitives, not a mutation framework.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_atomic(path: Path, content: str) -> None:
    """Create or modify a file using a same-directory temporary replacement.

    The caller must check the authorized target and its expected preimage
    before invocation. Temporary-file cleanup must not mask the original error.
    """
    fd, temporary = tempfile.mkstemp(dir=str(path.parent), prefix=".oneshot-tmp-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(content)
        os.replace(temporary, path)
    finally:
        try:
            Path(temporary).unlink(missing_ok=True)
        except OSError:
            # The caller retains the operation checkpoint for reconciliation.
            # Cleanup failures must never conceal an interrupted operation.
            pass


def move_file(source: Path, destination: Path) -> None:
    """Move a prechecked file using the existing same-filesystem atomic primitive."""
    os.replace(source, destination)


def remove_file(path: Path) -> None:
    """Remove a prechecked regular file."""
    path.unlink()
