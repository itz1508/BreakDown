"""Read-only comparison of Scanner trace observations with accepted criteria.

Host owns the accepted criteria and verifies the Scanner receipt and source
revision before invoking this function. This helper does not certify receipts,
authorize changes, dispatch tools, or substitute for independent Build E2E.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass

from agent.contracts.common import DiagnosticStatus
from agent.contracts.scanner import (
    CriterionResult,
    CriterionValidity,
    ObservationState,
    ScannerOutcome,
    ScannerResult,
)

Scalar = bool | int | float | str


@dataclass(frozen=True, slots=True)
class AcceptedCheck:
    check_id: str
    target_ref: str
    expected_value: Scalar
    weight: int = 1


@dataclass(frozen=True, slots=True)
class ComparedCheck:
    check_id: str
    target_ref: str
    status: DiagnosticStatus
    reason: str


@dataclass(frozen=True, slots=True)
class ScanComparison:
    status: DiagnosticStatus
    checks: tuple[ComparedCheck, ...]
    drift_score: int | None
    criteria_digest: str
    limitations: tuple[str, ...]


def _validate_checks(checks: Sequence[AcceptedCheck]) -> tuple[AcceptedCheck, ...]:
    """Do not allow a malformed or empty caller-supplied acceptance set."""
    if len(checks) == 0 or len(checks) > 128:
        raise ValueError("accepted criteria must contain 1..128 checks")
    keys: set[tuple[str, str]] = set()
    validated: list[AcceptedCheck] = []
    for check in checks:
        if not isinstance(check, AcceptedCheck):
            raise ValueError("invalid accepted check")
        if (
            not isinstance(check.check_id, str)
            or not 1 <= len(check.check_id) <= 128
            or not isinstance(check.target_ref, str)
            or not 1 <= len(check.target_ref) <= 256
            or type(check.expected_value) not in (bool, int, float, str)
            or (type(check.expected_value) is float and not math.isfinite(check.expected_value))
            or (type(check.expected_value) is int and abs(check.expected_value) > 10**12)
            or (type(check.expected_value) is str and len(check.expected_value) > 512)
            or any(
                ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF
                for text in (
                    check.check_id,
                    check.target_ref,
                    check.expected_value if isinstance(check.expected_value, str) else "",
                )
                for char in text
            )
            or type(check.weight) is not int
            or not 1 <= check.weight <= 1_000_000
        ):
            raise ValueError("invalid accepted criterion fields")
        key = (check.check_id, check.target_ref)
        if key in keys:
            raise ValueError("duplicate accepted criterion")
        keys.add(key)
        validated.append(check)
    return tuple(validated)


def verify_all(result: ScannerResult, *, checks: Sequence[AcceptedCheck]) -> ScanComparison:
    """Compare the recorded observations; do not run a scan or re-authorize it.

    The caller must provide Host-accepted criteria and a Host-verified result.
    ``VALID`` means *this comparison* matched, not Build/E2E approval.
    Unknown, missing or insufficiently evidenced observations never pass.
    Drift is an unbounded weighted mismatch sum, or None if incomplete.
    """
    accepted = _validate_checks(checks)
    # Pydantic.model_copy(update=...) bypasses validators; check the boundary.
    if not isinstance(result, ScannerResult):
        raise ValueError("result must be a ScannerResult")
    result = ScannerResult.model_validate(result.model_dump(mode="json"))
    data = [
        {
            "check_id": check.check_id,
            "target_ref": check.target_ref,
            "expected_value": check.expected_value,
            "weight": check.weight,
        }
        for check in sorted(accepted, key=lambda c: (c.check_id, c.target_ref))
    ]
    digest = hashlib.sha256(
        json.dumps(
            {"version": 1, "checks": data},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()

    steps = {(step.check_id, step.target_ref): step for step in result.trace_steps}
    # Duplicate observations cannot satisfy a criterion even if one matches.
    duplicate_steps = len(steps) != len(result.trace_steps)
    compared: list[ComparedCheck] = []
    limitations: list[str] = []
    if duplicate_steps:
        limitations.append("duplicate_trace_observations")
    if (
        result.candidate_ref is None
        or result.registry_ref is None
        or not result.repository_identity
        or not result.task_id
        or not result.run_id
    ):
        limitations.append("scanner_identity_incomplete")
    if result.capabilities_not_checked or result.evidence_requests or result.limitation_reasons:
        limitations.append("scanner_coverage_incomplete")
    if (
        not result.requested_capabilities
        or len(result.requested_capabilities) != len(set(result.requested_capabilities))
        or len(result.capabilities_checked) != len(set(result.capabilities_checked))
        or set(result.requested_capabilities) != set(result.capabilities_checked)
        or result.outcome in (ScannerOutcome.BLOCKED, ScannerOutcome.PARTIAL, ScannerOutcome.NOT_RUN)
    ):
        limitations.append("scanner_execution_incomplete")

    mismatch_weight = 0
    incomplete = bool(limitations)
    has_mismatch = False
    for check in accepted:
        step = steps.get((check.check_id, check.target_ref))
        reason = ""
        status = DiagnosticStatus.UNCERTAINTY
        if duplicate_steps:
            reason = "ambiguous_trace"
        elif step is None:
            reason = "missing_trace"
        elif type(step.expected_value) is not type(check.expected_value) or step.expected_value != check.expected_value:
            reason = "expected_value_conflict"
        elif not step.required:
            reason = "required_criterion_was_optional"
        elif step.observation_state is ObservationState.UNKNOWN or step.criterion_result is CriterionResult.UNKNOWN:
            reason = "observation_unknown"
        elif step.criterion_result is CriterionResult.NOT_SATISFIED:
            status = DiagnosticStatus.NOT_VALID
            reason = "observed_mismatch"
            has_mismatch = True
            mismatch_weight += check.weight
        elif step.criterion_validity is CriterionValidity.VALID and step.evidence_refs:
            status = DiagnosticStatus.VALID
            reason = "observed_match"
        else:
            reason = "evidence_not_validated"
        if status is DiagnosticStatus.UNCERTAINTY:
            incomplete = True
        compared.append(ComparedCheck(check.check_id, check.target_ref, status, reason))

    accepted_keys = {(item.check_id, item.target_ref) for item in accepted}
    if any(
        (step.check_id, step.target_ref) not in accepted_keys
        and (
            step.criterion_result is not CriterionResult.SATISFIED
            or step.criterion_validity is not CriterionValidity.VALID
        )
        for step in result.trace_steps
    ):
        limitations.append("unmatched_unresolved_trace")
        incomplete = True
    if result.outcome is ScannerOutcome.FAIL and not has_mismatch:
        limitations.append("scanner_failure_not_explained_by_criteria")
        incomplete = True
    if result.outcome is ScannerOutcome.PASS and has_mismatch:
        limitations.append("scanner_outcome_contradicts_trace")
        incomplete = True
    if result.findings and not has_mismatch:
        limitations.append("scanner_findings_not_explained_by_criteria")
        incomplete = True

    status = (
        DiagnosticStatus.NOT_VALID
        if has_mismatch
        else DiagnosticStatus.UNCERTAINTY
        if incomplete
        else DiagnosticStatus.VALID
    )
    score = None if incomplete else mismatch_weight
    return ScanComparison(status, tuple(compared), score, digest, tuple(dict.fromkeys(limitations)))
