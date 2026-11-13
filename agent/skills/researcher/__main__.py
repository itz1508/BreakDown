"""Researcher role entry: python -m agent.skills.researcher.

Thin and fail-closed. Research execution is dispatched only by the Host
(system.host.skill_dispatch); this entry never self-authorizes or fabricates
a Research result. It reports the registered dispatch route and exits.
"""

from __future__ import annotations

import json

from agent.skills.shared.host.skill_dispatch import registered_skills

if __name__ == "__main__":
    routes = [r for r in registered_skills() if r["contract_role"] == "researcher"]
    print(json.dumps({"role": "researcher", "dispatch_routes": routes}, sort_keys=True, indent=2))
    print(
        "researcher.run() requires a Host-verified dispatch envelope "
        "(use: python -m agent run <task-id>); no standalone execution here.",
    )
    raise SystemExit(2)
