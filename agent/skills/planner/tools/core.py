"""Read-only Scanner and planning tool types."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    capability: str
    code: str
    status: str
    severity: str
    path: str
    line: int
    message: str
    evidence_digest: str


def evidence(
    root: Path,
    path: Path,
    line: int,
    code: str,
    capability: str,
    severity: str,
    message: str,
    status: str = "candidate",
) -> Finding:
    """Capture file digest so a later host can reconcile stale findings."""
    data = path.read_bytes()
    return Finding(
        capability,
        code,
        status,
        severity,
        path.relative_to(root).as_posix(),
        line,
        message,
        hashlib.sha256(data).hexdigest(),
    )
