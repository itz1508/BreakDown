"""Regression coverage for the repaired observability contract.

The pydantic ``Field`` import was dropped when EventStatus/ExecutionEvent
were relocated to the event store (fixed in aa0cdb23750a4e38c63ef4f9c11e75
4018d80a22). TraceContext must instantiate and serialize round-trip.
"""

from __future__ import annotations

from agents.skills.shared.contracts.workflow.system import observability


def test_trace_context_instantiates_and_serializes_round_trip() -> None:
    trace = observability.TraceContext(trace_id="trace-1", metadata={"key": "value"})

    restored = observability.TraceContext.model_validate_json(trace.model_dump_json())

    assert restored.trace_id == "trace-1"
    assert restored.metadata == {"key": "value"}
    assert restored == trace


def test_trace_context_rejects_unknown_fields() -> None:
    import pytest

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        observability.TraceContext.model_validate({"trace_id": "t", "unexpected": 1})
