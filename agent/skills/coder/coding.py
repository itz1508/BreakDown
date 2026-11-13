"""Standalone CodeDesign capability: evidence questions after Research.

Adapted from the deep-module ideas in mattpocock/skills:
https://github.com/mattpocock/skills/tree/main/skills/engineering/codebase-design

This existing pure question-generation logic is independent of Auditor's
execution entrypoint. It does not correlate Research evidence with source,
create complete CodeDesign candidates, dispatch a stage, or issue receipts.
Planning owns subsequent design decisions; Host owns trusted authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.skills.auditor.contracts.code_design import CodeDesign


IntentOrigin = Literal[
    "existing_implementation_gap",
    "new_feature",
    "compatibility_change",
    "migration",
    "recovery_requirement",
]


@dataclass(frozen=True, slots=True)
class DesignQuestion:
    """A review question, not a finding or proof of implementation quality."""

    key: str
    question: str
    evidence_needed: str
    concern_if_unresolved: str


# The sequence is deliberate: establish the existing interface and ownership
# before proposing a new seam or removing a layer. Questions require observed
# evidence; their presence does not imply that a defect exists.
_BASE_QUESTIONS: tuple[DesignQuestion, ...] = (
    DesignQuestion(
        "existing-contract",
        "What must callers know about the interface: types, invariants, ordering, errors and performance?",
        "Public interfaces, consumers, contract definitions, and observed behavior.",
        "Simplifying a signature may silently discard a required contract.",
    ),
    DesignQuestion(
        "module-depth",
        "Does the module hide meaningful behavior while reducing the knowledge demanded of callers?",
        "Owned behavior, public operations, caller setup and cross-module changes.",
        "An extra wrapper can increase the interface cost without adding leverage.",
    ),
    DesignQuestion(
        "locality-and-deletion",
        "If this module disappeared, would its responsibility spread into multiple consumers?",
        "Call sites, forwarding paths, duplicate logic and change history where available.",
        "Deleting a shallow wrapper is useful only when it does not duplicate behavior or violate ownership.",
    ),
    DesignQuestion(
        "seam-placement",
        "What actually varies at this seam, and why must that variation remain isolated?",
        "Existing implementations, provider differences, test substitutes and security or deployment constraints.",
        "Adapter count alone cannot establish whether a seam is necessary or unnecessary.",
    ),
    DesignQuestion(
        "dependency-strategy",
        "Which dependencies are in-process, locally substitutable, remote-owned or external?",
        "Dependency graph, actual integration ownership, available fixtures and failure modes.",
        "Unjustified injection or hardcoded providers can both undermine isolation.",
    ),
    DesignQuestion(
        "ownership-and-authority",
        "Does the proposed design keep stage authority and side effects with their established owners?",
        "Role dispatch, CodeDesign/Planning contracts, host gates, effect executor and tool registry.",
        "A skill must not issue receipts, grant permissions, freeze plans, dispatch builds or write source.",
    ),
    DesignQuestion(
        "behavior-preservation",
        "What interfaces, persisted representations and callers must remain compatible?",
        "Existing wire fields, migrations, consumers, source checkpoints and accepted requirements.",
        "Renaming a Python symbol does not authorize a wire or storage migration.",
    ),
    DesignQuestion(
        "test-surface",
        "Can the intended behavior be verified through the interface and its observable effects?",
        "Behavioral tests, contract fixtures, negative cases, integration and E2E criteria.",
        "Do not delete security, regression, interruption or recovery coverage merely because a test is internal.",
    ),
    DesignQuestion(
        "failure-and-recovery",
        "What happens on errors, cancellation, retries, partial effects and resumption?",
        "Failure injection, checkpoints, idempotence, reconciliation and operator-visible errors.",
        "A simpler interface that hides unhandled failures is not an improvement.",
    ),
    DesignQuestion(
        "design-alternatives",
        "Were meaningful alternatives compared for leverage, locality, operational cost and change scope?",
        "Current approach, at least one feasible alternative when trade-offs are material, and rejection rationale.",
        "Do not force parallel-agent exploration or extra abstractions for trivial changes.",
    ),
)

_ORIGIN_QUESTIONS: dict[IntentOrigin, tuple[DesignQuestion, ...]] = {
    "existing_implementation_gap": (
        DesignQuestion(
            "gap-causality",
            "Does the proposed design correct the observed defect at its producing owner?",
            "Audit findings, source references, dependent consumers and regression fixture.",
            "A cosmetic refactor can leave the original defect unresolved.",
        ),
    ),
    "new_feature": (
        DesignQuestion(
            "feature-placement",
            "Which existing owner should provide the feature, and what evidence justifies any new module?",
            "Ownership and conflict inspections, existing extension points and required callers.",
            "New files or layers require a demonstrated capability gap, not a naming preference.",
        ),
    ),
    "compatibility_change": (
        DesignQuestion(
            "compatibility-matrix",
            "What versions, protocols, callers and persisted data remain supported?",
            "Version constraints, contract consumers, migration need and compatibility tests.",
            "A local refactor can break external compatibility despite unit tests.",
        ),
    ),
    "migration": (
        DesignQuestion(
            "migration-safety",
            "How do existing and target representations coexist, roll back and reconcile?",
            "Migration plan, persisted schemas, reader/writer compatibility and recovery fixtures.",
            "Renaming or deleting legacy data without a verified migration is destructive.",
        ),
    ),
    "recovery_requirement": (
        DesignQuestion(
            "recovery-observability",
            "Can an interrupted attempt be reconciled before retrying or resuming?",
            "Durable checkpoints, attempt identity, side-effect observations and chaos fixtures.",
            "Unproven retry safety can produce duplicate or contradictory effects.",
        ),
    ),
}


def review_questions(design: CodeDesign) -> tuple[DesignQuestion, ...]:
    """Return evidence questions for an existing, validated CodeDesign candidate.

    This does not read the repository, infer facts from missing evidence, choose a
    disposition, create Build actions, or issue a verification result. The
    Audit Discovery caller must inspect source evidence and preserve unresolved
    questions in its existing CodeDesign candidate. Planning evaluates that
    candidate and separately records CodeDesignReview and DesignDecision.
    """
    origin = design.intent_origin
    if origin not in _ORIGIN_QUESTIONS:
        raise ValueError(f"unsupported CodeDesign intent_origin: {origin!r}")
    return _BASE_QUESTIONS + _ORIGIN_QUESTIONS[origin]


__all__ = ["DesignQuestion", "review_questions"]
