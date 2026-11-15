"""Debug detectors: diagnostics only — syntax errors and duplicate candidates.

Every detector is static: ``ast.parse`` for syntax, AST-normalized function
fingerprints for duplicate candidates. Nothing scanned is ever imported or
executed, and a module that raises on import is scanned exactly like any
other text file.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

from system.scanner._index import backend_repo
from system.scanner._types import EngineOutcome, SystemScanFinding, SystemScanReport, Verdict

_PARSE_ERROR = "syntax-error"
_DUPLICATE_CANDIDATE = "duplicate-candidate"


def _function_fingerprint(source: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """A normalized fingerprint of a function body: names and shapes, not text."""
    normalized = ast.dump(
        ast.Module(body=node.body, type_ignores=[]),
        include_attributes=False,
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _syntax_findings(index: dict[str, Any], root: Path) -> tuple[list[SystemScanFinding], bool]:
    findings: list[SystemScanFinding] = []
    parse_failed = False
    for entry in index["entries"]:
        if not entry.relative_path.endswith(".py"):
            continue
        path = root / entry.relative_path
        try:
            source = path.read_bytes()
        except OSError:
            parse_failed = True
            continue
        try:
            ast.parse(source, filename=entry.relative_path)
        except SyntaxError as exc:
            parse_failed = True
            findings.append(
                SystemScanFinding(
                    detector=_PARSE_ERROR,
                    severity="blocking",
                    path=entry.relative_path,
                    message=f"syntax error: {exc.msg}",
                    line=exc.lineno,
                )
            )
    return findings, parse_failed


def _duplicate_findings(index: dict[str, Any], root: Path) -> list[SystemScanFinding]:
    seen: dict[str, tuple[str, str]] = {}
    findings: list[SystemScanFinding] = []
    for entry in index["entries"]:
        if not entry.relative_path.endswith(".py"):
            continue
        path = root / entry.relative_path
        try:
            tree = ast.parse(path.read_bytes(), filename=entry.relative_path)
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fingerprint = _function_fingerprint("", node)
                previous = seen.get(fingerprint)
                if previous is not None:
                    findings.append(
                        SystemScanFinding(
                            detector=_DUPLICATE_CANDIDATE,
                            severity="diagnostic",
                            path=entry.relative_path,
                            message=(
                                f"function '{node.name}' matches '{previous[1]}' "
                                f"({previous[0]}); a candidate, not an error"
                            ),
                            line=node.lineno,
                            confidence="medium",
                        )
                    )
                else:
                    seen[fingerprint] = (entry.relative_path, node.name)
    return findings


def scan_debug(target: str | Path, *, max_file_bytes: int | None = None) -> SystemScanReport:
    """Run the debug detectors over a target tree and return the report."""
    root = Path(target)
    try:
        index = backend_repo(root) if max_file_bytes is None else backend_repo(root, max_file_bytes=max_file_bytes)
    except NotADirectoryError:
        return SystemScanReport(
            target=str(root),
            mode="debug",
            outcome=EngineOutcome.BLOCKED,
            verdict=Verdict.INDETERMINATE,
            files_scanned=0,
            manifest_hash=None,
            entries=(),
            findings=(
                SystemScanFinding(
                    detector="backend_repo",
                    severity="blocking",
                    path=str(root),
                    message="scan target is not a directory",
                ),
            ),
        )

    findings, parse_failed = _syntax_findings(index, root)
    findings.extend(_duplicate_findings(index, root))
    findings.sort(key=lambda f: (f.detector, f.path, f.line or 0, f.message))

    unreadable = index["unreadable"]
    blocking = tuple(f for f in findings if f.severity == "blocking")
    if index["files_scanned"] == 0:
        outcome = EngineOutcome.INCOMPLETE
        verdict = Verdict.NOT_VALID
        findings = list(
            (
                *findings,
                SystemScanFinding(
                    detector="backend_repo",
                    severity="blocking",
                    path="",
                    message="zero files scanned; an empty scope can never be valid",
                ),
            )
        )
    elif blocking:
        # Parse errors and other blocking findings are definitive: outcome
        # incomplete (some checks could not run over the file), verdict
        # not_valid (blocking findings exist).
        outcome = EngineOutcome.INCOMPLETE if (unreadable or parse_failed) else EngineOutcome.COMPLETE
        verdict = Verdict.NOT_VALID
    elif unreadable or parse_failed:
        outcome = EngineOutcome.INCOMPLETE
        verdict = Verdict.INDETERMINATE
    else:
        outcome = EngineOutcome.COMPLETE
        verdict = Verdict.VALID

    return SystemScanReport(
        target=str(root),
        mode="debug",
        outcome=outcome,
        verdict=verdict,
        files_scanned=index["files_scanned"],
        manifest_hash=index["manifest_hash"],
        entries=index["entries"],
        findings=tuple(findings),
    )
