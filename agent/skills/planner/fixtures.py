"""Pure fixture-draft preparation from an existing candidate specification.

No tests, approval, receipt issuance, or runtime validation are performed.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.skills.planner.types import CandidateSpecification


@dataclass(frozen=True)
class FixtureDraft:
    fixture_id: str
    oracle_ref: str
    oracle_provenance: str
    test_inputs: str
    expected_results: tuple[str, ...]
    status: str = "draft_unverified"


def prepare(candidate: CandidateSpecification) -> tuple[FixtureDraft, ...]:
    """Copy declared fixtures; do not manufacture missing or observed results."""
    if not hasattr(candidate, "build_spec") or not hasattr(candidate.build_spec, "fixtures"):
        raise TypeError("candidate requires build_spec.fixtures attribute")
    source = candidate.build_spec.fixtures
    ids = [fixture.fixture_id for fixture in source]
    if len(set(ids)) != len(ids):
        raise ValueError("fixture IDs must be unique")
    return tuple(
        FixtureDraft(
            fixture_id=f.fixture_id,
            oracle_ref=f.oracle_ref,
            oracle_provenance=f.oracle_provenance,
            test_inputs=f.test_inputs,
            expected_results=f.expected_results,
        )
        for f in source
    )
