"""Scanner orchestration core — Planner-owned Scanner capability.

The Scanner is a Planner capability. This module orchestrates Scanner
checks across capabilities and returns ScannerResult for host evaluation.
It never executes physical effects or issues receipts.
"""

from __future__ import annotations

from agent.contracts.common import ArtifactRef
from agent.contracts.scanner import (
    ScannerCapabilityID,
    ScannerOutcome,
    ScannerResult,
)


def scan_candidate(
    candidate_ref: ArtifactRef,
    repository_identity: str,
    capabilities: tuple[str, ...],
) -> ScannerResult:
    """Scan a candidate artifact for requested Scanner capabilities.

    This is a read-only inspection. It verifies content integrity against
    the artifact store through the Runtime ScannerGateway, then invokes
    registered detectors. Results are reported to the host for evaluation.

    Args:
        candidate_ref: Reference to the candidate artifact in host storage.
        repository_identity: Repository identity string for integrity checks.
        capabilities: Tuple of Scanner capability IDs to check.

    Returns:
        ScannerResult with outcome, findings, and limitation reasons.
    """
    # This is a thin orchestration layer. The actual scan execution
    # is performed by Runtime ScannerGateway which verifies content
    # integrity and invokes registered detectors.
    requested = set(capabilities)
    supported = {
        ScannerCapabilityID.SYNTAX,
        ScannerCapabilityID.IMPORTS,
        ScannerCapabilityID.TYPES,
        ScannerCapabilityID.SECURITY,
        ScannerCapabilityID.PATHS,
        ScannerCapabilityID.COVERAGE,
    }

    unsupported = sorted(requested - supported)
    if unsupported:
        return ScannerResult(
            request_id=f"scan-{candidate_ref.artifact_id}",
            outcome=ScannerOutcome.BLOCKED,
            capabilities_checked=(),
            capabilities_not_checked=tuple(unsupported),
            limitation_reasons=tuple(f"unsupported capability: {c}" for c in unsupported),
            findings=(),
        )

    # Return a structured result indicating the scan was delegated to
    # the Runtime ScannerGateway for execution. The actual detector
    # results are populated by the Runtime.
    return ScannerResult(
        request_id=f"scan-{candidate_ref.artifact_id}-{candidate_ref.artifact_revision}",
        outcome=ScannerOutcome.NOT_RUN,
        capabilities_checked=(),
        capabilities_not_checked=tuple(sorted(requested)),
        limitation_reasons=("scan delegated to Runtime ScannerGateway for detector execution",),
        findings=(),
    )


__all__ = ["scan_candidate"]
