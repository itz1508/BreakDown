"""Preferred CodeDesign API; stable legacy wire fields remain readable.

Database and Vector Search schema renaming requires a separately verified migration.
"""

from agent.skills.auditor.contracts._discovery import (
    AuditDiscoveryPackage,
    CodeDesign,
    CompatibilityChangeIntent,
    ExistingGapIntent,
    MigrationIntent,
    NewFeatureIntent,
    RecoveryRequirementIntent,
)
from agent.skills.planner.contracts.specification import CodeDesignReview, IntentDisposition

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
