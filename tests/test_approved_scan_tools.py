"""Approved bounded capability probe and trace comparison; no fixtures or network."""

from __future__ import annotations

import sys

import pytest

from agent.skills.tools.sys_scan import sys_scan
from agent.skills.tools.verify_all import AcceptedCheck, verify_all
from contracts.workflow.common import ArtifactRef, DiagnosticStatus
from contracts.workflow.planner.scanner import (
    CriterionResult,
    CriterionValidity,
    ObservationState,
    ScannerOutcome,
    ScannerResult,
    ScannerTraceStep,
)


def _ref(label: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_id=label,
        artifact_revision=1,
        artifact_digest="a" * 64,
        contract_id="test_artifact",
        contract_version="1.0",
        serializer_profile="jcs",
    )


def _result(*, observed: bool | None = True, extra_trace: bool = False) -> ScannerResult:
    if observed is None:
        criterion = CriterionResult.UNKNOWN
        observation_state = ObservationState.UNKNOWN
    else:
        criterion = CriterionResult.SATISFIED if observed else CriterionResult.NOT_SATISFIED
        observation_state = ObservationState.KNOWN
    step = ScannerTraceStep(
        check_id="dependency_present",
        target_ref="candidate@1",
        rule_version="1",
        scanner_version="1",
        observation_state=observation_state,
        observed_value=observed,
        expected_value=True,
        criterion_result=criterion,
        criterion_validity=CriterionValidity.VALID if observed is True else CriterionValidity.NOT_VALID,
        evidence_refs=("artifact:verified-step",) if observed is True else (),
    )
    extras = (
        (
            ScannerTraceStep(
                check_id="extra_check",
                target_ref="candidate@1",
                rule_version="1",
                scanner_version="1",
                observation_state=ObservationState.UNKNOWN,
                observed_value=None,
                expected_value=True,
                criterion_result=CriterionResult.UNKNOWN,
                criterion_validity=CriterionValidity.NOT_VALID,
            ),
        )
        if extra_trace
        else ()
    )
    outcome = (
        ScannerOutcome.PASS
        if observed is True
        else ScannerOutcome.FAIL
        if observed is False
        else ScannerOutcome.BLOCKED
    )
    return ScannerResult(
        request_id="scan-1",
        outcome=outcome,
        task_id="task-1",
        run_id="run-1",
        repository_identity="commit:abc",
        requested_capabilities=("dependency_readiness",),
        capabilities_checked=("dependency_readiness",) if observed is not None else (),
        capabilities_not_checked=() if observed is not None else ("dependency_readiness",),
        candidate_ref=_ref("candidate"),
        registry_ref=_ref("registry"),
        trace_steps=(step, *extras),
    )


def test_sys_scan_does_not_install_instrumentation():
    before = getattr(sys, "monitoring", None)
    assert sys_scan() == {"monitoring_available": hasattr(sys, "monitoring")}
    assert sys_scan([]) == {}
    assert getattr(sys, "monitoring", None) is before
    with pytest.raises(ValueError):
        sys_scan(["monitoring_available", "unknown"])
    with pytest.raises(ValueError):
        sys_scan("monitoring_available")


def test_exact_accepted_trace_is_valid_read_only():
    criteria = [AcceptedCheck("dependency_present", "candidate@1", True)]
    r = verify_all(_result(), checks=criteria)
    assert r.status is DiagnosticStatus.VALID
    assert r.drift_score == 0
    assert not r.limitations
    assert len(r.criteria_digest) == 64
    assert verify_all(_result(), checks=criteria) == r


def test_known_mismatch_reports_weighted_drift():
    r = verify_all(
        _result(observed=False),
        checks=[AcceptedCheck("dependency_present", "candidate@1", True, weight=91)],
    )
    assert r.status is DiagnosticStatus.NOT_VALID
    assert r.drift_score == 91
    assert r.checks[0].reason == "observed_mismatch"


@pytest.mark.parametrize("observed", [True, None])
def test_unaccepted_or_unknown_evidence_cannot_pass(observed):
    r = verify_all(
        _result(observed=observed),
        checks=[AcceptedCheck("other_check", "candidate@1", True)],
    )
    assert r.status is DiagnosticStatus.UNCERTAINTY
    assert r.drift_score is None


def test_missing_evidence_cannot_pass():
    r = verify_all(
        _result(observed=None),
        checks=[AcceptedCheck("dependency_present", "candidate@1", True)],
    )
    assert r.status is DiagnosticStatus.UNCERTAINTY
    assert r.drift_score is None


def test_declared_expectation_conflicts_with_accepted_criteria():
    r = verify_all(
        _result(),
        checks=[AcceptedCheck("dependency_present", "candidate@1", False)],
    )
    assert r.status is DiagnosticStatus.UNCERTAINTY
    assert r.checks[0].reason == "expected_value_conflict"


def test_unmatched_unresolved_trace_cannot_pass():
    r = verify_all(
        _result(extra_trace=True),
        checks=[AcceptedCheck("dependency_present", "candidate@1", True)],
    )
    assert r.status is DiagnosticStatus.UNCERTAINTY
    assert "unmatched_unresolved_trace" in r.limitations


def test_invalid_or_duplicate_criteria_rejected():
    accepted = AcceptedCheck("dependency_present", "candidate@1", True)
    with pytest.raises(ValueError, match="duplicate"):
        verify_all(_result(), checks=[accepted, accepted])
    with pytest.raises(ValueError, match="1..128"):
        verify_all(_result(), checks=[])
    with pytest.raises(ValueError, match="invalid accepted criterion"):
        verify_all(_result(), checks=[AcceptedCheck("dependency_present", "candidate@1", float("nan"))])


def test_forged_model_copy_cannot_bypass_trace_validation():
    bad_step = _result().trace_steps[0].model_copy(update={"criterion_result": CriterionResult.NOT_SATISFIED})
    forged = _result().model_copy(update={"trace_steps": (bad_step,)})
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        verify_all(forged, checks=[AcceptedCheck("dependency_present", "candidate@1", True)])


def test_unmatched_unvalidated_satisfied_trace_cannot_pass():
    base = _result()
    extra = ScannerTraceStep(
        check_id="extra_check",
        target_ref="candidate@1",
        rule_version="1",
        scanner_version="1",
        observation_state=ObservationState.KNOWN,
        observed_value=True,
        expected_value=True,
        criterion_result=CriterionResult.SATISFIED,
        criterion_validity=CriterionValidity.NOT_VALID,
    )
    result = base.model_copy(update={"trace_steps": (*base.trace_steps, extra)})
    report = verify_all(result, checks=[AcceptedCheck("dependency_present", "candidate@1", True)])
    assert report.status is DiagnosticStatus.UNCERTAINTY
    assert report.drift_score is None
    assert "unmatched_unresolved_trace" in report.limitations


def test_duplicate_scanner_capabilities_cannot_pass():
    base = _result()
    duplicate = base.model_copy(
        update={
            "requested_capabilities": ("dependency_readiness", "dependency_readiness"),
            "capabilities_checked": ("dependency_readiness", "dependency_readiness"),
        }
    )
    report = verify_all(duplicate, checks=[AcceptedCheck("dependency_present", "candidate@1", True)])
    assert report.status is DiagnosticStatus.UNCERTAINTY
    assert "scanner_execution_incomplete" in report.limitations


def test_criteria_digest_is_independent_of_supplied_order_and_covers_weights():
    result = _result()
    accepted = AcceptedCheck("dependency_present", "candidate@1", True)
    other = AcceptedCheck("extra", "candidate@1", False)
    left = verify_all(result, checks=[accepted, other])
    right = verify_all(result, checks=[other, accepted])
    assert left.criteria_digest == right.criteria_digest
    weighted = verify_all(result, checks=[AcceptedCheck("dependency_present", "candidate@1", True, 2), other])
    assert weighted.criteria_digest != left.criteria_digest


def test_no_acceptance_result_claimed_for_unevidenced_matched_trace():
    base = _result()
    unevidenced = base.trace_steps[0].model_copy(
        update={
            "criterion_validity": CriterionValidity.NOT_VALID,
            "evidence_refs": (),
        }
    )
    altered = base.model_copy(update={"trace_steps": (unevidenced,)})
    report = verify_all(altered, checks=[AcceptedCheck("dependency_present", "candidate@1", True)])
    assert report.status is DiagnosticStatus.UNCERTAINTY
    assert report.drift_score is None


def test_missing_or_duplicate_traces_never_produce_valid():
    check = [AcceptedCheck("dependency_present", "candidate@1", True)]
    original = _result()
    for altered in (
        original.model_copy(update={"trace_steps": ()}),
        original.model_copy(update={"trace_steps": original.trace_steps * 2}),
    ):
        outcome = verify_all(altered, checks=check)
        assert outcome.status is DiagnosticStatus.UNCERTAINTY
        assert outcome.drift_score is None


def test_malformed_unicode_or_control_criteria_fail_closed():
    checks = [
        AcceptedCheck("\ud800", "candidate@1", True),
        AcceptedCheck("dependency_present", "candidate\n@1", True),
        AcceptedCheck("dependency_present", "candidate@1", "malformed\udfff"),
    ]
    for criterion in checks:
        with pytest.raises(ValueError, match="invalid accepted criterion"):
            verify_all(_result(), checks=[criterion])
