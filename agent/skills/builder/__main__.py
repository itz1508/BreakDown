"""Builder role entry: python -m agent.skills.builder.

Thin and fail-closed. Build effects execute only through the Host admission and
Runtime effect executor (agent.skills.shared.host.skill_dispatch); this entry never
self-authorizes. It reports the registered dispatch route and exits.
"""

from __future__ import annotations

import json

from agent.skills.shared.host.skill_dispatch import registered_skills

if __name__ == "__main__":
    routes = [r for r in registered_skills() if r["contract_role"] == "builder"]
    print(json.dumps({"role": "builder", "dispatch_routes": routes}, sort_keys=True, indent=2))
    print(
        "builder.run() requires a Host-verified dispatch envelope and an "
        "admission receipt; no standalone execution here.",
    )
    raise SystemExit(2)
