"""Append-only event log: storage order is the truth, never timestamps."""

from __future__ import annotations

from agents.shared.events.event import Event, create_event

__all__ = ["Event", "create_event"]
