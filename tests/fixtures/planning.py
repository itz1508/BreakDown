"""Planning records shared by the scanner E2E test and the cache benchmark.

The records are fixtures for *inputs* only. Every observation in the tests is
produced by the real ScannerGateway over a real ArtifactStore.
"""

from __future__ import annotations

from agent.skills.planner.contracts.specification import (
    BuildSpecification,
    CandidateSpecification,
    CreateAction,
    PlanningRecord,
)
from agent.skills.shared.contracts.workflow.common import ArtifactRef
from agent.skills.shared.storage.canonical_serialization import SERIALIZER_PROFILE


def artifact_ref(artifact_id: str, revision: int, digest: str, contract_id: str = "planning") -> ArtifactRef:
    return ArtifactRef(
        artifact_id=artifact_id,
        artifact_revision=revision,
        artifact_digest=digest,
        contract_id=contract_id,
        contract_version="1.0",
        serializer_profile=SERIALIZER_PROFILE,
    )


def make_planning_record() -> PlanningRecord:
    """Candidate with one unsatisfied dependency, used as the Scanner input."""
    action_base = {
        "requirement_ids": ("REQ-001",),
        "acceptance_criteria_ids": ("AC-001",),
        "code_intent_ids": ("intent-1",),
        "preconditions": ("source exists",),
        "validation_steps": ("test dependency",),
        "expected_result": "implemented",
        "recovery_requirement": "restore original",
        "target_conflict_check_ref": "fixture-ref",
    }
    producer = CreateAction(action_id="producer", target_path="producer.py", **action_base)
    consumer = CreateAction(action_id="consumer", target_path="consumer.py", depends_on=("absent",), **action_base)
    return PlanningRecord(
        task_id="task-001",
        run_id="run-001",
        stage_revision=1,
        audit_ref=artifact_ref("audit", 1, "b" * 64, "audit"),
        candidate=CandidateSpecification(
            candidate_id="candidate-001",
            specification_revision=1,
            build_spec=BuildSpecification(
                spec_id="spec-001",
                objective="implement dependencies",
                actions=(producer, consumer),
            ),
        ),
    )


def revised_record(original: PlanningRecord) -> PlanningRecord:
    """Same candidate with the dependency satisfied, at stage revision 2."""
    producer, consumer = original.candidate.build_spec.actions
    fixed = consumer.model_copy(update={"depends_on": ("producer",)})
    specification = original.candidate.build_spec.model_copy(update={"actions": (producer, fixed)})
    candidate = original.candidate.model_copy(update={"specification_revision": 2, "build_spec": specification})
    return original.model_copy(update={"stage_revision": 2, "candidate": candidate})
