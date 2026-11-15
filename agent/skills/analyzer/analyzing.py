"""Analyzer entrypoint: review code, logical, structure, broken path, mismatch wire, miswire.

Delegates to the gap analysis functions already in _structural.py.
This is a skill entrypoint wrapper, not new logic.
"""

from __future__ import annotations

from agent.contracts.validation.structural import (
    ConcernCell,
    ReferenceNeed,
    SourceDeclaration,
    TraceStep,
    concern_gaps,
    reference_gaps,
    registry_resolution_gaps,
    trace_gaps,
)


def review_code(
    needs: tuple[ReferenceNeed, ...],
    sources: tuple[SourceDeclaration, ...],
) -> list[str]:
    """Review: every external reference must have an accountable owner and evidence."""
    return reference_gaps(needs, sources)


def review_logical(
    steps: tuple[TraceStep, ...],
    external: tuple[SourceDeclaration, ...],
) -> list[str]:
    """Review: temporal producer-before-consumer closure and effect gates."""
    return trace_gaps(steps, external)


def review_structure(
    stages: tuple[str, ...],
    cells: tuple[ConcernCell, ...],
) -> list[str]:
    """Review: coverage matrix is complete only with evidenced owners or reasoned N/A."""
    return concern_gaps(stages, cells)


def detect_broken_path(
    needs: tuple[ReferenceNeed, ...],
    sources: tuple[SourceDeclaration, ...],
) -> list[str]:
    """Detect: references with no producer (broken path)."""
    defined = {s.name for s in sources if s.owner and s.evidence_ref}
    return [f"{n.consumer}: no producer for {n.name}" for n in needs if n.name not in defined]


def detect_mismatch_wire(
    required_registry_ids: tuple[str, ...],
    sources: tuple[SourceDeclaration, ...],
) -> list[str]:
    """Detect: registry entries without effect-time resolver (mismatch wire)."""
    return registry_resolution_gaps(required_registry_ids, sources)


def detect_miswire(
    steps: tuple[TraceStep, ...],
    external: tuple[SourceDeclaration, ...],
) -> list[str]:
    """Detect: consumer before producer, undeclared outputs, missing gates (miswire)."""
    errors: list[str] = []
    available = {item.name for item in external if item.owner and item.evidence_ref}
    for index, step in enumerate(steps):
        for missing in sorted(step.needs - available):
            errors.append(f"{step.step_id}: nothing produces {missing}")
        if step.effect and not step.gate:
            errors.append(f"{step.step_id}: effect {step.effect} has no gate")
        for output in sorted(set(step.ephemeral_outputs) - step.produces):
            errors.append(f"{step.step_id}: undeclared ephemeral output {output}")
        available.update(step.produces)
    return errors


def run(
    *,
    needs: tuple[ReferenceNeed, ...] = (),
    sources: tuple[SourceDeclaration, ...] = (),
    steps: tuple[TraceStep, ...] = (),
    stages: tuple[str, ...] = (),
    cells: tuple[ConcernCell, ...] = (),
    required_registry_ids: tuple[str, ...] = (),
) -> dict[str, list[str]]:
    """Run all review passes and return findings by category."""
    return {
        "review_code": review_code(needs, sources),
        "review_logical": review_logical(steps, sources),
        "review_structure": review_structure(stages, cells),
        "detect_broken_path": detect_broken_path(needs, sources),
        "detect_mismatch_wire": detect_mismatch_wire(required_registry_ids, sources),
        "detect_miswire": detect_miswire(steps, sources),
    }