"""scan_predict: experimental. Compare a baseline manifest against a target tree.

Experimental per the scanner plan (section 12): the input contract is a
baseline manifest (the ``entries`` of a previous ``backend_repo`` run) and a
change set expressed as additions, modifications and removals. Where the
baseline cannot answer, the report is ``indeterminate`` — never a guess.
"""

from __future__ import annotations

from pathlib import Path

from system.scanner._index import backend_repo
from system.scanner._types import (
    EngineOutcome,
    FileEntry,
    SystemScanFinding,
    SystemScanReport,
    Verdict,
)

_PREDICT = "predict"


def scan_predict(
    baseline: tuple[FileEntry, ...],
    target: str | Path,
    *,
    max_file_bytes: int | None = None,
) -> SystemScanReport:
    """Compare a baseline index against the current tree.

    Findings are one per addition, modification and removal. A baseline entry
    whose content cannot be interpreted for the change is reported as
    ``indeterminate`` evidence, not silently accepted.
    """
    root = Path(target)
    index = backend_repo(root) if max_file_bytes is None else backend_repo(root, max_file_bytes=max_file_bytes)
    current = {entry.relative_path: entry for entry in index["entries"]}
    base = {entry.relative_path: entry for entry in baseline}

    findings: list[SystemScanFinding] = []
    for path in sorted(set(base) - set(current)):
        findings.append(
            SystemScanFinding(detector=_PREDICT, severity="diagnostic", path=path, message="removed since baseline")
        )
    for path in sorted(set(current) - set(base)):
        findings.append(
            SystemScanFinding(detector=_PREDICT, severity="diagnostic", path=path, message="added since baseline")
        )
    for path in sorted(set(base) & set(current)):
        if base[path].sha256 != current[path].sha256:
            findings.append(
                SystemScanFinding(
                    detector=_PREDICT,
                    severity="diagnostic",
                    path=path,
                    message="modified since baseline",
                )
            )

    if not base:
        outcome = EngineOutcome.INCOMPLETE
        verdict = Verdict.INDETERMINATE
        findings.append(
            SystemScanFinding(
                detector=_PREDICT,
                severity="diagnostic",
                path="",
                message="empty baseline: prediction evidence is insufficient",
            )
        )
    else:
        outcome = EngineOutcome.COMPLETE
        verdict = Verdict.INDETERMINATE  # prediction is always advisory evidence

    return SystemScanReport(
        target=str(root),
        mode="predict",
        outcome=outcome,
        verdict=verdict,
        files_scanned=index["files_scanned"],
        manifest_hash=index["manifest_hash"],
        entries=index["entries"],
        findings=tuple(findings),
    )
