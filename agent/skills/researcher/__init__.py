"""Researcher skill — research execution, sourced claims, evidence requests.

Ownership:
    Research execution, sourced claims, evidence requests. The Researcher
    executes research tasks against configured MCP transports, produces
    sourced ResearchRecord artifacts, and never advances workflow stages
    on its own. All receipts and stage transitions are issued by the
    Runtime host.

Tools:
    research_catalog — versioned synthetic catalog with deterministic matching

Runtime integration:
    Results are reported through the HostDispatchResult envelope. The
    Runtime validates, persists, and advances stages based on Researcher
    output.
"""

from agent.skills.researcher.run import post_dispatch, pre_dispatch

__all__ = ["post_dispatch", "pre_dispatch"]
