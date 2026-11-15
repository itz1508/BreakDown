"""Scanner capability request and finding shapes."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from agent.contracts.common import ArtifactRef, ContractModel, Sha256
from agent.contracts.host import ReceiptRef
from agent.contracts.planning_coverage import PlanningCoverage


class ScannerOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


class ScannerCapabilityID(StrEnum):
    SYNTAX = "syntax"
    IMPORTS = "imports"
    TYPES = "types"
    SECURITY = "security"
    PATHS = "paths"
    COVERAGE = "coverage"


class ScannerRequest(ContractModel):
    task_id: str = Field(min_length=1)
    candidate_artifact: ArtifactRef
    specification_revision: int = Field(ge=1)
    specification_digest: Sha256
    repository_source: str = Field(min_length=1)
    requested_capabilities: tuple[str, ...] = Field(min_length=1)


class ScannerFinding(ContractModel):
    finding_id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    message: str = Field(min_length=1)
    location: str = ""
    evidence_ref: str = ""


class ScannerResult(ContractModel):
    request_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    candidate_ref: ArtifactRef
    registry_ref: ArtifactRef
    repository_identity: str | None = None
    outcome: ScannerOutcome
    capabilities_checked: tuple[str, ...] = ()
    capabilities_not_checked: tuple[str, ...] = ()
    findings: tuple[ScannerFinding, ...] = ()
    findings_artifact_id: str | None = None
    findings_artifact_digest: Sha256 | None = None
    limitation_reasons: tuple[str, ...] = ()
    planning_coverage: PlanningCoverage | None = None


class ScannerEvidence(ContractModel):
    """Evidence record linking a scanner result to its host receipt."""

    result_ref: ArtifactRef
    receipt_ref: ReceiptRef
