"""Use the existing host-managed MCP Research implementation."""

from __future__ import annotations

from agent.skills.planner.tools._structural import HostDispatchEnvelope


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: ResearchArguments) -> dict[str, object]:
    """Run an existing task; never fabricate a Research result or receipt."""
    if context.research_service is None:
        raise ValueError("Research service is not configured")
    if context.research_service.host.state_root.resolve() != context.host.state_root.resolve():
        raise ValueError("Research service and dispatch host use different state roots")
    # External dependency: mvp.research_host is host-owned.
    # Fails closed with ModuleNotFoundError if the host runtime is not installed.
    from mvp.research_host import execute_research

    return execute_research(context.research_service, envelope.task_id)
