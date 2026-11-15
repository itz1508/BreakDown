"""Detect known static recovery and multi-process admission limitations."""

from __future__ import annotations

from pathlib import Path

from agent.skills.auditor.checks.core import Finding, evidence, safe_read_text


def scan_recovery(root: Path, scope: Path) -> list[Finding]:
    service = root / "mvp" / "service.py"
    host = root / "mvp" / "research_host.py"
    if scope != root and not any(path.is_relative_to(scope) for path in (service, host)):
        return []
    findings: list[Finding] = []
    if service.is_file():
        content = safe_read_text(root, service)
        if (
            "_active_requests: set[str]" in content
            and "self._active_guard = Lock()" in content
            and "_ResearchAdmissionStore" not in content
        ):
            findings.append(
                evidence(
                    root,
                    service,
                    1,
                    "IN_PROCESS_ADMISSION_ONLY",
                    "recovery",
                    "high",
                    "Research slot uses process-local admission; "
                    "cross-process safety requires independent verification.",
                )
            )
    if host.is_file():
        content = safe_read_text(root, host)
        if "reconcile host state before retry" in content and "def _reconcile_research(" not in content:
            findings.append(
                evidence(
                    root,
                    host,
                    1,
                    "RECOVERY_RECONCILIATION_REQUIRED",
                    "recovery",
                    "medium",
                    "Research retry is explicitly blocked pending host reconciliation after partial effects.",
                    status="verified_observation",
                )
            )
    return findings
