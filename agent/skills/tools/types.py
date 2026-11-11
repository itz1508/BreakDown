"""Deprecated: import from agent.contracts.scanner and agent.contracts.common instead."""

from agent.contracts.common import DiagnosticStatus
from agent.contracts.scanner import (
    CriterionResult,
    CriterionValidity,
    ObservationState,
    ScannerOutcome,
)

__all__ = [
    "CriterionResult",
    "CriterionValidity",
    "DiagnosticStatus",
    "ObservationState",
    "ScannerOutcome",
]
