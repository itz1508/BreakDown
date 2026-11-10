"""Read-only diagnostic exchange models. No new stage or receipt authority."""

from __future__ import annotations

import re
from enum import StrEnum
from pydantic import Field, model_validator

from contracts.workflow.common import ArtifactRef, ContractModel, DiagnosticStatus, Sha256


class FrameEvidence(ContractModel):
    path: str = Field(min_length=1, max_length=240)
    line: int = Field(ge=1)
    function: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")

    @model_validator(mode="after")
    def relative_location(self) -> FrameEvidence:
        if (self.path.startswith("/") or "\\" in self.path
            or re.match(r"^[A-Za-z]:", self.path)
            or ".." in self.path.split("/")
            or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in self.path)):
            raise ValueError("diagnostic frame path must be normalized relative metadata")
        return self


class NormalizedException(ContractModel):
    """Exception metadata only: never stack locals or unredacted messages."""

    type: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    module_name: str | None = Field(
        default=None, max_length=160, pattern=r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$"
    )
    errno: int | None = None
    frames: tuple[FrameEvidence, ...] = Field(default=(), max_length=12)
    cause_types: tuple[str, ...] = Field(default=(), max_length=4)
    frames_truncated: bool = False
    chain_truncated: bool = False


class DossierFinding(ContractModel):
    finding_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:/-]+$")
    capability: str = Field(min_length=1, max_length=96, pattern=r"^[A-Za-z0-9_.:/-]+$")
    severity: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")


class DiagnosticDossier(ContractModel):
    """Transient evidence projection; digest verification is not a Host receipt."""

    task_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    run_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    exception: NormalizedException
    source_ref: ArtifactRef | None = None
    scanner_result_ref: ArtifactRef | None = None
    historical_refs: tuple[ArtifactRef, ...] = Field(default=(), max_length=3)
    findings: tuple[DossierFinding, ...] = Field(default=(), max_length=16)
    evidence_keys: tuple[str, ...] = Field(default=(), max_length=6)
    evidence_status: DiagnosticStatus = DiagnosticStatus.UNCERTAINTY
    limitations: tuple[str, ...] = Field(default=(), max_length=6)

    @model_validator(mode="after")
    def consistent_evidence(self) -> DiagnosticDossier:
        if len(set(self.evidence_keys)) != len(self.evidence_keys):
            raise ValueError("duplicate evidence key")
        expected = tuple(
            f"{role}:{ref.artifact_digest}"
            for role, ref in (("source", self.source_ref), ("scanner", self.scanner_result_ref))
            if ref is not None
        )
        if self.evidence_keys != expected:
            raise ValueError("Dossier evidence keys must bind exact supplied artifact references")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", reason) for reason in self.limitations):
            raise ValueError("untrusted diagnostic limitation code")
        if self.evidence_status is DiagnosticStatus.VALID:
            raise ValueError("diagnostic Dossiers cannot certify evidence validity")
        return self


class Recommendation(ContractModel):
    """LLM output: proposed hypotheses only; no approvals or edits."""

    hypothesis: str = Field(min_length=1, max_length=600)
    recommended_checks: tuple[str, ...] = Field(min_length=1, max_length=6)
    supporting_evidence_keys: tuple[str, ...] = Field(default=(), max_length=6)

    @model_validator(mode="after")
    def limited_checks(self) -> Recommendation:
        if any(not item.strip() or len(item) > 200 for item in self.recommended_checks):
            raise ValueError("recommended checks must be bounded and nonempty")
        if len(set(self.supporting_evidence_keys)) != len(self.supporting_evidence_keys):
            raise ValueError("duplicate recommendation evidence")
        return self


class RecommendationStatus(StrEnum):
    PROPOSED = "proposed"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


class DiagnosticReview(ContractModel):
    dossier: DiagnosticDossier
    recommendation_status: RecommendationStatus
    recommendation: Recommendation | None = None
    reason_code: str = Field(default="", max_length=64)
    provider_id: str = Field(default="", max_length=100, pattern=r"^[A-Za-z0-9_./:-]*$")
    model_id: str = Field(default="", max_length=160, pattern=r"^[A-Za-z0-9_./:-]*$")
    request_digest: Sha256 | None = None
    verification: str = "not_run"

    @model_validator(mode="after")
    def enforce_non_authority(self) -> DiagnosticReview:
        if self.verification != "not_run":
            raise ValueError("diagnostic review cannot claim verification")
        if (self.recommendation_status is RecommendationStatus.PROPOSED) != (self.recommendation is not None):
            raise ValueError("recommendation required only for proposed state")
        if (
            self.recommendation is not None
            and not set(self.recommendation.supporting_evidence_keys).issubset(self.dossier.evidence_keys)
        ):
            raise ValueError("diagnostic recommendation cites unverified evidence")
        return self
