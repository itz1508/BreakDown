"""Build execution tool — executes admitted Build actions through Runtime.

The Builder delegates physical effect execution to the Runtime
EffectExecutor. This module formats admitted BuildAction requests and
reports execution results through the HostDispatch envelope.
"""

from __future__ import annotations

from agent.contracts.build import BuildActionExecution, BuildActionStatus
from agent.contracts.host import BuildAdmissionReceipt
from agent.contracts.planning import BuildAction


def execute_admitted(
    action: BuildAction,
    admission_receipt: BuildAdmissionReceipt,
) -> BuildActionExecution:
    """Prepare an admitted BuildAction for Runtime execution.

    This does not execute the effect itself — the Runtime EffectExecutor
    performs the physical operation after rechecking preconditions at
    effect time. This module validates that the action is covered by the
    admission receipt and returns a PENDING execution record.

    Args:
        action: The BuildAction to execute.
        admission_receipt: Host-issued admission receipt authorizing the action.

    Returns:
        BuildActionExecution with PENDING status for Runtime to execute.

    Raises:
        ValueError: If the action is not covered by the admission receipt.
    """
    if action.action_id not in admission_receipt.authorized_action_ids:
        raise ValueError(
            f"Action {action.action_id} is not authorized by admission receipt {admission_receipt.admission_id}."
        )
    return BuildActionExecution(
        action_id=action.action_id,
        status=BuildActionStatus.PENDING,
    )


__all__ = ["execute_admitted"]
