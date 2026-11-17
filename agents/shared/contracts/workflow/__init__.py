"""OneShot contract schemas — Pydantic v2 typed primitives and stage records.

Primitives live in ``agents.shared.base`` (single copy); this package
re-exports them for existing import paths.
"""

from agents.shared.base import (
    ArtifactRef,
    ContractModel,
    CriterionId,
    EvidenceRef,
    RequirementId,
    Sha256,
    StepResult,
    StepStatus,
)

__all__ = [
    "ArtifactRef",
    "ContractModel",
    "CriterionId",
    "EvidenceRef",
    "RequirementId",
    "Sha256",
    "StepResult",
    "StepStatus",
]
