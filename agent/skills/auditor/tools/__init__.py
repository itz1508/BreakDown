"""Auditor skill tools — read-only inspection implementations.

Tools are pure functions that take a repository root and scope and return
Finding tuples. They never mutate state or issue receipts.
"""

from collections.abc import Callable
from pathlib import Path

from agent.skills.auditor.tools.core import AuditResult, Finding
from agent.skills.auditor.tools.paths import scan_paths
from agent.skills.auditor.tools.security import scan_security
from agent.skills.auditor.tools.state import scan_state


def scan(root: Path, scope: str = ".", capabilities: tuple[str, ...] = ()) -> AuditResult:
    """Run auditor tools against a repository scope.

    Args:
        root: Repository root path
        scope: Repository scope name
        capabilities: Specific capabilities to scan; runs all if empty

    Returns:
        Dictionary of results including findings and disposition
    """
    scanners: dict[str, Callable[[Path, Path], list[Finding]]] = {
        "paths": scan_paths,
        "security": scan_security,
        "state": scan_state,
    }

    requested = capabilities or tuple(scanners)
    unknown = set(requested) - set(scanners)
    if unknown:
        raise ValueError(f"unknown auditor capabilities: {', '.join(sorted(unknown))}")

    root = Path(root).resolve()
    target = (root / scope).resolve(strict=True) if scope else root

    if not target.is_dir():
        raise ValueError("audit scope must be a directory")

    if not target.is_relative_to(root):
        raise ValueError("audit scope escapes repository root")

    findings: list[Finding] = []
    limitations = [
        "Static observations are not runtime or E2E verification.",
        "Only Python and literal frontend API route patterns are inspected; dynamic wiring requires runtime evidence.",
    ]
    executed: list[str] = []
    for name in dict.fromkeys(requested):
        try:
            findings.extend(scanners[name](root, target))
            executed.append(name)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            limitations.append(f"{name} not completed: {type(exc).__name__}")

    findings.sort(key=lambda f: (f.capability, f.path, f.line, f.code))

    if len(executed) != len(set(requested)):
        disposition = "blocked"
    elif findings:
        disposition = "findings_open"
    else:
        disposition = "not_e2e_verified"

    return AuditResult(
        root=str(root),
        scope=target.relative_to(root).as_posix(),
        requested_capabilities=tuple(requested),
        executed_capabilities=tuple(executed),
        findings=tuple(findings),
        limitations=tuple(limitations),
        disposition=disposition,
    )


__all__ = ["scan", "scan_paths", "scan_security", "scan_state"]
