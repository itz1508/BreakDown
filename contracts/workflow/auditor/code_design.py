"""Preferred CodeDesign API; stable legacy wire fields remain readable.

Database and Vector Search schema renaming requires a separately verified migration.
"""

from contracts.workflow.auditor._discovery import (
    AuditDiscoveryPackage,
    CodeDesign,
    CompatibilityChangeIntent,
    ExistingGapIntent,
    MigrationIntent,
    NewFeatureIntent,
    RecoveryRequirementIntent,
)
from contracts.workflow.planner.specification import CodeDesignReview, IntentDisposition

__all__ = [
    "AuditDiscoveryPackage",
    "CodeDesign",
    "CodeDesignReview",
    "CompatibilityChangeIntent",
    "ExistingGapIntent",
    "IntentDisposition",
    "MigrationIntent",
    "NewFeatureIntent",
    "RecoveryRequirementIntent",
]
