"""Engine-internal types for the system scanner.

Private to this package: the public surface is the re-export in
``system.scanner.__init__``. The report carries no timestamps so identical
trees produce byte-identical output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EngineOutcome(StrEnum):
    """Whether the required checks actually ran."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    BLOCKED = "blocked"
    ERROR = "error"


class Verdict(StrEnum):
    """Diagnostic verdict derived from the outcome and the findings."""

    VALID = "valid"
    NOT_VALID = "not_valid"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class FileEntry:
    """One indexed file: POSIX relative path, content hash and size."""

    relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class SystemScanFinding:
    """One scanner finding. Diagnostics carry confidence; blocking do not."""

    detector: str
    severity: str  # "blocking" or "diagnostic"
    path: str
    message: str
    line: int | None = None
    confidence: str | None = None  # "high" | "medium" | "low"


@dataclass(frozen=True)
class SystemScanReport:
    """The full result of one scan mode over one target."""

    target: str
    mode: str
    outcome: EngineOutcome
    verdict: Verdict
    files_scanned: int
    manifest_hash: str | None
    entries: tuple[FileEntry, ...]
    findings: tuple[SystemScanFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        import dataclasses

        return {
            "target": self.target,
            "mode": self.mode,
            "outcome": self.outcome.value,
            "verdict": self.verdict.value,
            "files_scanned": self.files_scanned,
            "manifest_hash": self.manifest_hash,
            "entries": [dataclasses.asdict(e) for e in self.entries],
            "findings": [dataclasses.asdict(f) for f in self.findings],
        }
