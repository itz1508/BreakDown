"""Preflight detectors: retired paths and import boundaries, caller-configured.

The retirement ledger is supplied by the caller (decision D5: the approved
ledger lives in ``scripts/check_retired_paths.py``); the engine never imports
it. The same applies to boundary rules: the caller passes the prefixes a
scoped package must not import.
"""

from __future__ import annotations

import ast
from pathlib import Path

from system.scanner._index import backend_repo
from system.scanner._types import EngineOutcome, SystemScanFinding, SystemScanReport, Verdict

_RETIRED_PATH = "retired-path"
_BOUNDARY_IMPORT = "boundary-import"


def scan_preflight(
    target: str | Path,
    *,
    retired_prefixes: tuple[str, ...] = (),
    boundary_rules: dict[str, str] | None = None,
) -> SystemScanReport:
    """Run preflight detectors over a target tree.

    ``retired_prefixes``: tracked-path prefixes that must not exist under the
    target. ``boundary_rules``: maps a directory prefix (posix, relative to the
    target) to a forbidden import prefix — a module under that directory may
    not import a module starting with the forbidden prefix.
    """
    if boundary_rules is None:
        boundary_rules = {}
    root = Path(target)
    try:
        index = backend_repo(root)
    except NotADirectoryError:
        return SystemScanReport(
            target=str(root),
            mode="preflight",
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

    findings: list[SystemScanFinding] = []
    for entry in index["entries"]:
        for prefix in retired_prefixes:
            if entry.relative_path.startswith(prefix):
                findings.append(
                    SystemScanFinding(
                        detector=_RETIRED_PATH,
                        severity="blocking",
                        path=entry.relative_path,
                        message=f"path restores a retired prefix: {prefix}",
                    )
                )
        for scope_prefix, forbidden in boundary_rules.items():
            if not entry.relative_path.startswith(scope_prefix) or not entry.relative_path.endswith(".py"):
                continue
            try:
                tree = ast.parse((root / entry.relative_path).read_bytes(), filename=entry.relative_path)
            except (SyntaxError, OSError):
                continue
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules = [node.module]
                for module in modules:
                    if module.startswith(forbidden):
                        findings.append(
                            SystemScanFinding(
                                detector=_BOUNDARY_IMPORT,
                                severity="blocking",
                                path=entry.relative_path,
                                message=f"import of {module} crosses the {scope_prefix} boundary",
                                line=getattr(node, "lineno", None),
                            )
                        )

    findings.sort(key=lambda f: (f.detector, f.path, f.line or 0, f.message))
    blocking = tuple(f for f in findings if f.severity == "blocking")
    outcome = EngineOutcome.COMPLETE if index["files_scanned"] > 0 else EngineOutcome.INCOMPLETE
    if outcome is EngineOutcome.INCOMPLETE:
        verdict = Verdict.INDETERMINATE
    elif blocking:
        verdict = Verdict.NOT_VALID
    else:
        verdict = Verdict.VALID

    return SystemScanReport(
        target=str(root),
        mode="preflight",
        outcome=outcome,
        verdict=verdict,
        files_scanned=index["files_scanned"],
        manifest_hash=index["manifest_hash"],
        entries=index["entries"],
        findings=tuple(findings),
    )
