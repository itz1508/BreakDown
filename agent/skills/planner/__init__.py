"""Planner skill — code review, design, refactoring plans, Scanner, gap resolution.

Ownership:
    Code review, design, refactoring plans, Scanner capability execution,
    gap resolution, and fixture definitions. The Planner produces
    BuildSpecification candidates and PlanningRecord artifacts. It never
    issues trusted receipts or authorizes Build operations — those remain
    host-owned through the Runtime.

Tools:
    scanner_engine — orchestrates Scanner checks across capabilities
    completeness — surfaces unfinished implementation markers
    contract_scanner — checks internal import targets
    dependencies — reproducibility checks for declared dependencies
    frontend_api — frontend integration observations
    integration — Audit exposure within Research path
    recovery — static recovery and admission limitations
    verification — discovers verification surfaces
    wiring — compares frontend API fetches to FastAPI routes
    gap_analysis — structural gap analysis for planning candidates

Runtime integration:
    Planning output is reported through HostDispatchResult. The Runtime
    host validates, freezes specifications, and issues Build admission.
"""

from agent.skills.planner.run import post_dispatch, pre_dispatch

__all__ = ["post_dispatch", "pre_dispatch"]
