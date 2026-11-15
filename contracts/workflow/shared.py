"""Legacy compatibility re-export of the shared OneShot primitives.

The canonical single copy lives in ``agents.shared.base``. This module
exists only so historical ``contracts.workflow.shared`` imports keep
resolving to the very same classes - enum identity (``is``) and Pydantic
model identity are preserved because no second definition remains.
"""

from __future__ import annotations

from agents.shared.base import (
    ArtifactEnvelope,
    ArtifactRef,
    AssessmentId,
    ContractModel,
    CoverageStatus,
    CriteriaStatus,
    CriterionId,
    DecisionId,
    DiagnosticStatus,
    EvidenceId,
    EvidenceRef,
    FindingId,
    IssueId,
    OperationState,
    ProposalState,
    RequirementId,
    ReviewId,
    Sha256,
    SpecificationState,
    StepResult,
    StepStatus,
    UpstreamBinding,
)

__all__ = [
    "ArtifactEnvelope",
    "ArtifactRef",
    "AssessmentId",
    "ContractModel",
    "CoverageStatus",
    "CriteriaStatus",
    "CriterionId",
    "DecisionId",
    "DiagnosticStatus",
    "EvidenceId",
    "EvidenceRef",
    "FindingId",
    "IssueId",
    "OperationState",
    "ProposalState",
    "RequirementId",
    "ReviewId",
    "Sha256",
    "SpecificationState",
    "StepResult",
    "StepStatus",
    "UpstreamBinding",
]
