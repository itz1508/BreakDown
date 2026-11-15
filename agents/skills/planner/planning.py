"""Planner entrypoints: candidate creation intent only.

The structural scanner was retired into the separate system/scanner engine;
planning owns interpretation, not scanner execution.
"""

from __future__ import annotations

from typing import Any


class PlanningPipelineNotActive(RuntimeError):
    """The declared planning pipeline has no trusted execution adapter yet."""


def create(request: object, context: object) -> Any:
    """Do not create a candidate until approved operations are truly installed."""
    if request is None or context is None:
        raise ValueError("planning.create requires a request and context")
    raise PlanningPipelineNotActive(
        "plan.yaml is declarative; a trusted, separately approved pipeline "
        "executor is required before planning.create can produce candidates"
    )
