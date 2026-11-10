"""Behavior-preserving tests for standalone CodeDesign question generation."""

from types import SimpleNamespace

import pytest

from agent.skills.code_design.code_design import review_questions


def test_code_design_questions_have_evidence_first_sequence() -> None:
    questions = review_questions(SimpleNamespace(intent_origin="existing_implementation_gap"))
    assert questions[0].key == "existing-contract"
    assert questions[-1].key == "gap-causality"
    assert len({q.key for q in questions}) == len(questions)
    with pytest.raises(ValueError, match="unsupported CodeDesign"):
        review_questions(SimpleNamespace(intent_origin="unregistered"))


def test_skill_import_does_not_run_questions() -> None:
    from agent.skills.code_design import code_design

    assert code_design.review_questions is review_questions
