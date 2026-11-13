"""Planner role entry: python -m agent.skills.planner.

Thin and fail-closed. Planning/Scanner execution is dispatched only by the Host
(system.host.skill_dispatch); this entry never self-authorizes. It reports the
registered dispatch route and exits. Fixtures stay draft-only via fixtures.py.
"""

from __future__ import annotations

import json

from agent.skills.shared.host.skill_dispatch import registered_skills

if __name__ == "__main__":
    routes = [r for r in registered_skills() if r["contract_role"] == "planner"]
    print(json.dumps({"role": "planner", "dispatch_routes": routes}, sort_keys=True, indent=2))
    print(
        "planner.run() requires a Host-verified dispatch envelope "
        "(use: python -m agent scan <task-id> <request.json>); no standalone execution here.",
    )
    raise SystemExit(2)
