"""Apply admitted Build actions only through the existing Runtime executor."""

from __future__ import annotations

from agent.contracts.build import BuildActionExecution
from agent.contracts.host import HostDispatchEnvelope
from agent.runtime.skill_dispatch import BuildArguments, SkillContext


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: BuildArguments) -> BuildActionExecution:
    """Delegate effect-time gates and checkpoints to Runtime; never self-authorize."""
    return context.build_executor().execute_admitted(
        action_id=arguments.action_id,
        action_kind=arguments.action_kind,
        admission_receipt=arguments.admission_receipt,
        target_path=arguments.target_path,
        source_path=arguments.source_path,
        content=arguments.content,
        expected_source_digest=arguments.expected_source_digest,
        wave=arguments.wave,
    )
