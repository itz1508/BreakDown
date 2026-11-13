"""Builder role entry: python -m agent.skills.builder.

Thin and fail-closed. Execution is dispatched only by the Host
(agent.host.skill_dispatch); this entry never self-authorizes. It reports the
registered dispatch route and exits.
"""

from __future__ import annotations

import json

from agent.host.skill_dispatch import registered_skills


def main() -> int:
    routes = [r for r in registered_skills() if r["contract_role"] == "builder"]
    print(json.dumps({"role": "builder", "dispatch_routes": routes}, sort_keys=True, indent=2))
    print(
        "builder.run() requires a Host-verified dispatch envelope; "
        "no standalone execution here.",
    )
    return 2
