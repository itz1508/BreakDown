"""System scanner: a read-only, static-analysis engine.

One scanner implementation, one authority for its reports. It never writes,
never imports or executes scanned code, and reports uncertainty instead of
silent validity. Evidence issuance is deliberately out of scope for this
package (separated for review).
"""

from __future__ import annotations

from system.scanner._debug import scan_debug
from system.scanner._index import backend_repo
from system.scanner._predict import scan_predict
from system.scanner._preflight import scan_preflight
from system.scanner._types import (
    EngineOutcome,
    FileEntry,
    SystemScanFinding,
    SystemScanReport,
    Verdict,
)

__all__ = [
    "EngineOutcome",
    "FileEntry",
    "SystemScanFinding",
    "SystemScanReport",
    "Verdict",
    "backend_repo",
    "scan_debug",
    "scan_predict",
    "scan_preflight",
]
