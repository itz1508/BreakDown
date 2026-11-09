"""Specification Freeze — host-frozen BuildSpecification before Build admission.

The Runtime host freezes a BuildSpecification candidate into an immutable
artifact. Once frozen, any change to upstream artifacts invalidates the
Package Lock. Only the host may freeze specifications.
"""

from __future__ import annotations

from agent.contracts.common import ArtifactRef
from agent.contracts.host import FreezeReceipt, ReceiptRef
from agent.contracts.planning import CandidateSpecification
from agent.runtime.artifact_store import ArtifactStore
from agent.runtime.receipt_store import ReceiptStore


class SpecificationFreezeError(Exception):
    """Raised when specification freezing fails."""


class SpecificationFreeze:
    """Host-owned specification freeze authority.

    Freezes a BuildSpecification into a content-addressed artifact and
    issues a FreezeReceipt binding the candidate to the frozen spec.
    """

    def __init__(
        self,
        artifact_store: ArtifactStore,
        receipt_store: ReceiptStore,
    ) -> None:
        self._store = artifact_store
        self._receipts = receipt_store

    def freeze(
        self,
        freeze_id: str,
        candidate: CandidateSpecification,
        scanner_receipt_ref: ReceiptRef,
        repository_identity_ref: str,
        authorization_receipt_ref: ReceiptRef,
        issuer_id: str = "host",
    ) -> FreezeReceipt:
        """Freeze a BuildSpecification candidate and issue a FreezeReceipt.

        Args:
            freeze_id: Unique identifier for this freeze operation.
            candidate: The CandidateSpecification to freeze.
            scanner_receipt_ref: Host-issued scanner receipt ref.
            repository_identity_ref: Repository identity reference string.
            authorization_receipt_ref: Host-issued authorization receipt ref.
            issuer_id: Must be "host".

        Returns:
            FreezeReceipt binding the candidate to the frozen spec artifact.

        Raises:
            SpecificationFreezeError: If issuer is not host or freeze fails.
        """
        if issuer_id != "host":
            raise SpecificationFreezeError("only host may freeze specifications")

        # Store the candidate specification as an immutable artifact
        candidate_id = f"candidate-{freeze_id}"
        candidate_digest = self._store.put_immutable(
            candidate,
            candidate_id,
            1,
            "candidate_specification",
            "1.0",
        )
        candidate_ref = ArtifactRef(
            artifact_id=candidate_id,
            artifact_revision=1,
            artifact_digest=candidate_digest,
            contract_id="candidate_specification",
            contract_version="1.0",
            serializer_profile="rfc8785-jcs-sha256-v1",
        )

        # Store the build spec as a separate frozen artifact
        spec_id = f"frozen-spec-{freeze_id}"
        spec_digest = self._store.put_immutable(
            candidate.build_spec,
            spec_id,
            1,
            "build_specification",
            "1.0",
        )
        frozen_ref = ArtifactRef(
            artifact_id=spec_id,
            artifact_revision=1,
            artifact_digest=spec_digest,
            contract_id="build_specification",
            contract_version="1.0",
            serializer_profile="rfc8785-jcs-sha256-v1",
        )

        # Issue freeze receipt
        receipt_id = f"freeze-{freeze_id}"
        subject = (
            f"{candidate_ref.artifact_digest}:"
            f"{frozen_ref.artifact_digest}:"
            f"{scanner_receipt_ref.receipt_digest}:"
            f"{authorization_receipt_ref.receipt_digest}"
        )
        _, receipt_digest = self._receipts.issue_verified(receipt_id, issuer_id, subject)
        receipt = ReceiptRef(
            receipt_id=receipt_id,
            receipt_digest=receipt_digest,
            issuer_id=issuer_id,
        )

        return FreezeReceipt(
            candidate_ref=candidate_ref,
            frozen_ref=frozen_ref,
            scanner_receipt_ref=scanner_receipt_ref,
            repository_identity_ref=repository_identity_ref,
            authorization_receipt_ref=authorization_receipt_ref,
        )


__all__ = ["SpecificationFreeze", "SpecificationFreezeError"]
