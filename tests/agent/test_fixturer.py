"""Fixturer emits unverified drafts; it does not execute validation."""

import pytest

from agent.skills.fixturer.Fixturer import prepare
from contracts.workflow.planner.specification import (
    BuildSpecification,
    CandidateSpecification,
    FixtureSpecification,
)


def test_declared_fixture_is_preserved_without_execution():
    declared = FixtureSpecification(
        fixture_id="f1",
        oracle_ref="oracle:1",
        oracle_provenance="accepted-criterion",
        test_inputs="sample input",
        expected_results=("expected behavior",),
    )
    candidate = CandidateSpecification.model_construct(
        build_spec=BuildSpecification.model_construct(fixtures=(declared,))
    )
    drafts = prepare(candidate)
    assert len(drafts) == 1
    assert drafts[0].fixture_id == "f1"
    assert drafts[0].oracle_provenance == "accepted-criterion"
    assert drafts[0].expected_results == ("expected behavior",)
    assert drafts[0].status == "draft_unverified"


def test_missing_fixtures_are_not_invented():
    candidate = CandidateSpecification.model_construct(
        build_spec=BuildSpecification.model_construct(fixtures=())
    )
    assert prepare(candidate) == ()


def test_wrong_candidate_type_rejected():
    with pytest.raises(TypeError, match="typed CandidateSpecification"):
        prepare(object())
