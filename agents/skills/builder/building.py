"""Apply admitted Build actions only through the existing Runtime executor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.skills.builder.effect_executor import EffectExecutor
from agents.skills.shared.storage.artifact_store import ArtifactStore
from agents.skills.shared.storage.checkpoint_store import CheckpointStore
from agents.skills.shared.storage.receipt_store import ReceiptStore


def build_executor(state_root: str | Path, workspace_root: str | Path) -> EffectExecutor:
    """Construct the authorized Runtime executor over the given roots."""
    from agents.skills.shared.host.sys_policy_enforcer import AuthorizationEngine

    state = Path(state_root)
    workspace = Path(workspace_root)
    return EffectExecutor(
        authorization=AuthorizationEngine(allowed_roots=(str(workspace), str(state))),
        checkpoint_store=CheckpointStore(state),
        receipt_store=ReceiptStore(state),
        workspace_root=workspace,
        artifact_store=ArtifactStore(state),
    )


def execute_admitted(state_root: str | Path, workspace_root: str | Path, **arguments: Any) -> Any:
    """Delegate effect-time gates and checkpoints to the executor; never self-authorize."""
    return build_executor(state_root, workspace_root).execute_admitted(**arguments)
