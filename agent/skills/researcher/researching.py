"""Use the existing host-managed MCP Research implementation."""

from __future__ import annotations

from agent.skills.shared.contracts.workflow.system.host import HostDispatchEnvelope
from agent.skills.shared.host.skill_dispatch import ResearchArguments, SkillContext


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: ResearchArguments) -> dict[str, object]:
    """Run an existing task; never fabricate a Research result or receipt."""
    if context.research_service is None:
        raise ValueError("Research service is not configured")
    if context.research_service.host.state_root.resolve() != context.host.state_root.resolve():
        raise ValueError("Research service and dispatch host use different state roots")
    return context.research_service.execute_research(envelope.task_id)
