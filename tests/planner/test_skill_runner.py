"""Planner's Scanner path remains host-owned."""

from unittest.mock import Mock

import pytest

from agent.runtime.skill_dispatch import PlanningArguments
from agent.skills.planner.run import run


def test_scanner_dispatch_uses_bound_candidate() -> None:
    host = Mock()
    scan = Mock(run_id="run", candidate_ref=Mock(), repository_identity="git:abc",
                capabilities=("dependency_readiness",), gap_result_ref=Mock(), gap_receipt_ref=Mock())
    context = Mock(host=host)
    expected = object()
    host.scan_planning_candidate.return_value = expected
    assert run(context, Mock(task_id="task", run_id="run"), PlanningArguments(scan=scan)) is expected
    host.scan_planning_candidate.assert_called_once_with(
        task_id="task", run_id="run", candidate_ref=scan.candidate_ref,
        repository_identity="git:abc", capabilities=("dependency_readiness",),
        gap_result_ref=scan.gap_result_ref, gap_receipt_ref=scan.gap_receipt_ref,
    )
    host.receipt_store.issue_verified.assert_not_called()


def test_scanner_rejects_cross_run() -> None:
    host = Mock()
    with pytest.raises(ValueError, match="run does not match"):
        run(Mock(host=host), Mock(run_id="good"), PlanningArguments(scan=Mock(run_id="wrong")))
    host.scan_planning_candidate.assert_not_called()
