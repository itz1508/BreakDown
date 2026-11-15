"""Effect verification tool — verifies pre/post image digests and effect observations.

The Builder uses this tool to confirm that Build effects match expected
pre/post image digests. Verification results are reported to the Runtime
host, which issues operation receipts.
"""

from __future__ import annotations

from agent.contracts.build import BuildActionExecution, BuildActionStatus


def verify_effects(
    execution: BuildActionExecution,
    expected_pre_digest: str | None = None,
    expected_post_digest: str | None = None,
    actual_post_digest: str | None = None,
) -> BuildActionExecution:
    """Verify that Build effects match expected pre/post image digests.

    Args:
        execution: The BuildActionExecution to verify.
        expected_pre_digest: Expected pre-image digest (if applicable).
        expected_post_digest: Expected post-image digest (if applicable).
        actual_post_digest: Actual post-image digest observed after execution.

    Returns:
        Updated BuildActionExecution with COMPLETED, FAILED, or
        EFFECT_UNCERTAIN status.
    """
    if expected_post_digest is not None and actual_post_digest is not None:
        if actual_post_digest == expected_post_digest:
            return execution.model_copy(
                update={"status": BuildActionStatus.COMPLETED, "post_image_digest": actual_post_digest}
            )
        return execution.model_copy(
            update={
                "status": BuildActionStatus.EFFECT_UNCERTAIN,
                "error": (f"digest mismatch: expected {expected_post_digest}, got {actual_post_digest}"),
                "post_image_digest": actual_post_digest,
            }
        )
    if expected_post_digest is None and actual_post_digest is None:
        return execution.model_copy(update={"status": BuildActionStatus.COMPLETED})
    return execution.model_copy(update={"status": BuildActionStatus.EFFECT_UNCERTAIN})


__all__ = ["verify_effects"]
