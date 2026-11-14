"""Host Scanner persists a verified pass, ordered events, and no forgeable receipt.

The gap artifacts and the two detectors are fixtures; the structural-gap
verification, scanner gateway, check registry, artifact store, receipt store and
event ordering below are real.
"""

from __future__ import annotations

from typing import NamedTuple

import pytest

from agents.skills.planner.contracts.scanner import ScannerEvidence
from agents.skills.planner.scanner_evidence import verify_scanner_evidence
from agents.skills.shared.contracts.workflow.common import ArtifactRef
from agents.skills.shared.contracts.workflow.system.host import ReceiptRef
from agents.skills.shared.host.sys_controller import HostController
from tests.e2e.harness import create_task
from tests.fixtures.scanner import passing_scan
from tests.fixtures.structural_gap import passing_gap

pytestmark = pytest.mark.e2e

TASK_ID = "task-scanner"
RUN_ID = "run-scanner"
REPOSITORY = "repo-001"


class Scanned(NamedTuple):
    host: HostController
    candidate: ArtifactRef
    evidence: ScannerEvidence


def scanned_candidate(tmp_path) -> Scanned:
    host = HostController(tmp_path / "state")
    create_task(host, TASK_ID, RUN_ID)
    gap = passing_gap(host, TASK_ID, RUN_ID)
    candidate = gap.result.candidate_specification_ref
    assert candidate is not None
    return Scanned(host, candidate, passing_scan(host, gap))


def verify(scanned: Scanned):
    assert scanned.host.scanner_checks is not None
    return verify_scanner_evidence(
        scanned.host.artifact_store,
        scanned.host.receipt_store,
        scanned.evidence,
        scanned.candidate,
        scanned.host.scanner_checks,
        TASK_ID,
        RUN_ID,
        REPOSITORY,
    )


def test_scanner_pass_is_persisted_with_bound_receipt(tmp_path) -> None:
    scanned = scanned_candidate(tmp_path)
    result = verify(scanned)

    assert result.outcome.value == "pass"
    assert result.requested_capabilities == ("syntax", "types")
    ref = scanned.evidence.result_ref
    assert scanned.host.artifact_store.get_digest(ref.artifact_id, ref.artifact_revision) == ref.artifact_digest


def test_scanner_events_are_persisted_in_order(tmp_path) -> None:
    scanned = scanned_candidate(tmp_path)
    events = [event["event_type"] for event in scanned.host.event_store.list(TASK_ID)]
    assert events.count("scanner_started") == 1
    assert events.count("scanner_recorded") == 1
    assert events.count("scanner_completed") == 1
    assert events.index("scanner_started") < events.index("scanner_recorded") < events.index("scanner_completed")


def test_scanner_receipt_cannot_be_forged(tmp_path) -> None:
    scanned = scanned_candidate(tmp_path)
    assert scanned.host.scanner_checks is not None
    forged = scanned.evidence.model_copy(
        update={
            "receipt_ref": ReceiptRef(
                receipt_id=scanned.evidence.receipt_ref.receipt_id,
                receipt_digest="f" * 64,
                issuer_id="host",
            )
        }
    )
    with pytest.raises(ValueError, match="Scanner pass receipt is not verified"):
        verify_scanner_evidence(
            scanned.host.artifact_store,
            scanned.host.receipt_store,
            forged,
            scanned.candidate,
            scanned.host.scanner_checks,
            TASK_ID,
            RUN_ID,
            REPOSITORY,
        )
