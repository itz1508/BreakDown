"""Observability contracts — trace context.

EventStatus and ExecutionEvent are owned by the event store
(``agents/shared/storage/event_store.py``), their only consumer.
"""

from __future__ import annotations

from pydantic import Field

from agents.shared.base import ContractModel


class TraceContext(ContractModel):
    """Distributed trace linking for cross-stage observability."""

    trace_id: str = Field(min_length=1)
    group_id: str | None = None
    parent_span_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
