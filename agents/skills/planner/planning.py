"""Planner entrypoints: candidate creation intent and the Host-free Scanner."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from agents.skills.planner.scanner_gateway import ScannerGateway
from agents.skills.shared.storage.artifact_store import ArtifactStore

if TYPE_CHECKING:
    from agents.skills.planner.contracts.scanner import ScannerResult, ScannerRunInput


class PlanningPipelineNotActive(RuntimeError):
    """The declared planning pipeline has no trusted execution adapter yet."""


def create(request: object, context: object) -> Any:
    """Do not create a candidate until approved operations are truly installed."""
    if request is None or context is None:
        raise ValueError("planning.create requires a request and context")
    raise PlanningPipelineNotActive(
        "plan.yaml is declarative; a trusted, separately approved pipeline "
        "executor is required before planning.create can produce candidates"
    )


def scan(state_root: str | Path, request: ScannerRunInput) -> ScannerResult:
    """Run the structural scanner over the candidate and persist the result."""
    store = ArtifactStore(Path(state_root))
    gateway = ScannerGateway(store)
    return gateway.scan_exact(
        request.candidate_ref,
        request.repository_identity,
        request.capabilities,
    )
