"""Structural gap analysis for planning candidates.

This module decides whether a Planning candidate is structurally complete.
It is pure: host-only artifact verification, persistence, execution, and
receipt issuance remain in ``agent.runtime.host_gap_analyzer``.
"""

from __future__ import annotations

from agent.contracts.common import ArtifactRef, ContractModel, DiagnosticStatus, StepStatus
from agent.contracts.validation.structural import (
    ConcernCell,
    ReferenceNeed,
    SourceDeclaration,
    TraceStep,
    concern_gaps,
    reference_gaps,
    trace_gaps,
)


class WorkflowContractBundle(ContractModel):
    """Declared stages, cross-stage references, and persisted outputs."""

    stage_ids: tuple[str, ...]
    reference_needs: tuple[ReferenceNeed, ...] = ()
    persisted_output_slots: tuple[str, ...] = ()
    consumed_output_slots: tuple[str, ...] = ()
    terminal_output_slots: tuple[str, ...] = ()


class RegistrySnapshotSet(ContractModel):
    """Frozen capability registries and their effect-time resolvers."""

    sources: tuple[SourceDeclaration, ...] = ()
    required_registry_ids: tuple[str, ...] = ()


class WorkflowExecutionTrace(ContractModel):
    """Ordered workflow steps with dependencies, outputs, effects, and gates."""

    steps: tuple[TraceStep, ...]


class WorkflowConcernMatrix(ContractModel):
    """Required concern coverage for every declared workflow stage."""

    stages: tuple[str, ...]
    cells: tuple[ConcernCell, ...] = ()


class KnownCriticalBacktest(ContractModel):
    """One historical omission that the current analyzer must detect."""

    case_id: str
    case_evidence_ref: ArtifactRef
    reference_needs: tuple[ReferenceNeed, ...] = ()
    sources: tuple[SourceDeclaration, ...] = ()
    trace_steps: tuple[TraceStep, ...] = ()
    stages: tuple[str, ...] = ()
    concern_cells: tuple[ConcernCell, ...] = ()
    expected_findings: tuple[str, ...]


class GapBacktestCorpus(ContractModel):
    """Historical failures used to prevent regression in detection ability."""

    historical_cases: tuple[KnownCriticalBacktest, ...]


class SourceGroundedAnalysis(ContractModel):
    """Evidence that candidate capabilities were compared with actual source."""

    source_snapshot_ref: ArtifactRef
    evidence_refs: tuple[ArtifactRef, ...]
    completed: bool
    unresolved: tuple[str, ...] = ()


class ComparableSystemAnalysis(ContractModel):
    """Evidence that applicable comparable systems were checked."""

    evidence_refs: tuple[ArtifactRef, ...] = ()
    completed: bool
    not_applicable_reason: str = ""
    unresolved: tuple[str, ...] = ()


class WalkingSkeletonObservation(ContractModel):
    """Observed execution of the minimal complete workflow."""

    completed: bool
    executed_steps: tuple[str, ...] = ()
    evidence_ref: ArtifactRef | None = None
    error: str = ""


class StructuralGapRequest(ContractModel):
    """Exact immutable inputs for one candidate analysis."""

    task_id: str
    run_id: str
    request_id: str
    request_revision: int
    candidate_specification_ref: ArtifactRef
    workflow_contract_bundle_ref: ArtifactRef
    registry_snapshot_set_ref: ArtifactRef
    workflow_trace_ref: ArtifactRef
    concern_matrix_ref: ArtifactRef
    backtest_corpus_ref: ArtifactRef
    source_grounded_analysis_ref: ArtifactRef
    comparable_system_analysis_ref: ArtifactRef


class StructuralGapResult(ContractModel):
    """Result of a structural gap analysis."""

    task_id: str
    run_id: str
    request_id: str
    request_revision: int
    candidate_specification_ref: ArtifactRef
    diagnostic_status: DiagnosticStatus
    execution_status: StepStatus
    findings: tuple[str, ...] = ()
    reference_gaps: tuple[str, ...] = ()
    trace_gaps: tuple[str, ...] = ()
    concern_gaps: tuple[str, ...] = ()


def analyze_gap(
    request: StructuralGapRequest,
    workflow: WorkflowContractBundle,
    registry: RegistrySnapshotSet,
    trace: WorkflowExecutionTrace,
    matrix: WorkflowConcernMatrix,
    corpus: GapBacktestCorpus,
    grounded: SourceGroundedAnalysis,
    comparable: ComparableSystemAnalysis,
    skeleton: WalkingSkeletonObservation | None = None,
) -> StructuralGapResult:
    """Analyze structural gaps for a planning candidate.

    Returns a StructuralGapResult with diagnostic status and findings.
    Host persistence and receipt issuance remain in
    agent.runtime.host_gap_analyzer.
    """
    errors: list[str] = []

    # Reference gap checks
    ref_errors = reference_gaps(workflow.reference_needs, workflow.sources if hasattr(workflow, "sources") else ())
    errors.extend(ref_errors)

    # Trace gap checks
    trace_errors = trace_gaps(trace.steps, ())
    errors.extend(trace_errors)

    # Concern gap checks
    concern_errors = concern_gaps(matrix.stages, matrix.cells)
    errors.extend(concern_errors)

    diagnostic = DiagnosticStatus.VALID if not errors else DiagnosticStatus.NOT_VALID
    execution = StepStatus.COMPLETED if not errors else StepStatus.BLOCKED

    return StructuralGapResult(
        task_id=request.task_id,
        run_id=request.run_id,
        request_id=request.request_id,
        request_revision=request.request_revision,
        candidate_specification_ref=request.candidate_specification_ref,
        diagnostic_status=diagnostic,
        execution_status=execution,
        findings=tuple(errors),
        reference_gaps=tuple(ref_errors),
        trace_gaps=tuple(trace_errors),
        concern_gaps=tuple(concern_errors),
    )


class GapAnalyzer:
    """Canonical structural gap analyzer.

    Wraps :func:`analyze_gap` to provide a class-based interface used by
    ``agent.runtime.host_gap_analyzer.HostGapAnalyzer``.
    """

    def analyze(
        self,
        request: StructuralGapRequest,
        workflow: WorkflowContractBundle,
        registry: RegistrySnapshotSet,
        trace: WorkflowExecutionTrace,
        matrix: WorkflowConcernMatrix,
        corpus: GapBacktestCorpus,
        grounded: SourceGroundedAnalysis,
        comparable: ComparableSystemAnalysis,
        skeleton: WalkingSkeletonObservation | None = None,
    ) -> StructuralGapResult:
        """Run structural gap analysis and return the result."""
        return analyze_gap(
            request=request,
            workflow=workflow,
            registry=registry,
            trace=trace,
            matrix=matrix,
            corpus=corpus,
            grounded=grounded,
            comparable=comparable,
            skeleton=skeleton,
        )


__all__ = [
    "ComparableSystemAnalysis",
    "GapAnalyzer",
    "GapBacktestCorpus",
    "KnownCriticalBacktest",
    "RegistrySnapshotSet",
    "SourceGroundedAnalysis",
    "StructuralGapRequest",
    "StructuralGapResult",
    "WalkingSkeletonObservation",
    "WorkflowConcernMatrix",
    "WorkflowContractBundle",
    "WorkflowExecutionTrace",
    "analyze_gap",
]
