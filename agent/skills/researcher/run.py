"""Use the existing host-managed MCP Research implementation."""

from __future__ import annotations

from agent.contracts.host import HostDispatchEnvelope
from agent.runtime.skill_dispatch import ResearchArguments, SkillContext


def run(
    context: SkillContext, envelope: HostDispatchEnvelope, arguments: ResearchArguments
) -> dict[str, object]:
    """Run an existing task; never fabricate a Research result or receipt."""
    if context.research_service is None:
        raise ValueError("Research service is not configured")
    if context.research_service.host.state_root.resolve() != context.host.state_root.resolve():
        raise ValueError("Research service and dispatch host use different state roots")
    from mvp.research_host import execute_research

    return execute_research(context.research_service, envelope.task_id)
