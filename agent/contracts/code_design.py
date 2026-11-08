"""Preferred CodeDesign API; stable legacy wire fields remain readable.

Database and Vector Search schema renaming requires a separately verified migration.
"""

from agent.contracts.audit_discovery import (
    AuditDiscoveryPackage,
    CodeDesign,
    CompatibilityChangeIntent,
    ExistingGapIntent,
    MigrationIntent,
    NewFeatureIntent,
    RecoveryRequirementIntent,
)
from agent.contracts.planning import CodeDesignReview, IntentDisposition

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
