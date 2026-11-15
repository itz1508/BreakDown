"""Deprecated re-export shim: import from agent.contracts.* instead.

All types and functions have been remapped to canonical contract sources.
This file remains for backward compatibility only.
"""

from __future__ import annotations

# --- Contract base and primitives (from agent.contracts.common) ---
from agent.contracts.common import (
    ArtifactRef,
    AssessmentId,
    ContractModel,
    CriterionId,
    DecisionId,
    DiagnosticStatus,
    EvidenceId,
    EvidenceRef,
    FindingId,
    IssueId,
    OperationState,
    RequirementId,
    ReviewId,
    Sha256,
    SpecificationState,
    StepResult,
    StepStatus,
)

# --- Host types (from agent.contracts.host) ---
from agent.contracts.host import HostDispatchEnvelope, ReceiptRef

# --- Build types (from agent.contracts.build) ---
from agent.contracts.build import BuildActionExecution

# --- Tool registry types (from agent.contracts.tool_registry) ---
from agent.contracts.tool_registry import StageId, ToolId, ToolInvocation, safe_relative_path

# --- Structural types and gap functions (from agent.contracts.validation.structural) ---
from agent.contracts.validation.structural import (
    CONCERNS,
    ConcernCell,
    PersistenceDeclaration,
    ReferenceNeed,
    SourceDeclaration,
    TraceStep,
    concern_gaps,
    reference_gaps,
    registry_resolution_gaps,
    trace_gaps,
)

# --- Scanner types (from agent.contracts.scanner) ---
from agent.contracts.scanner import (
    CriterionResult,
    CriterionValidity,
    ObservationState,
    ScannerOutcome,
)

__all__ = [
    "ArtifactRef",
    "AssessmentId",
    "BuildActionExecution",
    "CONCERNS",
    "ConcernCell",
    "ContractModel",
    "CriterionId",
    "CriterionResult",
    "CriterionValidity",
    "DecisionId",
    "DiagnosticStatus",
    "EvidenceId",
    "EvidenceRef",
    "FindingId",
    "HostDispatchEnvelope",
    "IssueId",
    "ObservationState",
    "OperationState",
    "PersistenceDeclaration",
    "ReceiptRef",
    "ReferenceNeed",
    "RequirementId",
    "ReviewId",
    "ScannerOutcome",
    "Sha256",
    "SourceDeclaration",
    "SpecificationState",
    "StageId",
    "StepResult",
    "StepStatus",
    "ToolId",
    "ToolInvocation",
    "TraceStep",
    "concern_gaps",
    "reference_gaps",
    "registry_resolution_gaps",
    "safe_relative_path",
    "trace_gaps",
]
