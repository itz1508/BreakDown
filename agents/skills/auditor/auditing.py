"""Execute read-only source checks for the Auditor role."""

from __future__ import annotations

from pathlib import Path

from agents.skills.auditor.tools.core import AuditResult, scan


def run(
    workspace_root: str | Path,
    request: str,
    scope: str = ".",
    capabilities: tuple[str, ...] = (),
) -> AuditResult:
    """Return source-grounded findings without issuing receipts or modifying source."""
    return scan(
        Path(workspace_root),
        scope=scope,
        capabilities=capabilities,
        request=request,
    )
