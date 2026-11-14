# Planner — candidate planning and evidence review

**Mini-pipeline:** `plan.yaml#main` traces requirements, inspects patterns,
drafts a candidate before scanning, records findings, and calls
`agent.skills.planner.fixtures.prepare` for unverified fixture drafts. No
approval or freeze operation is defined.

**Python API:** `agent.skills.planner.planning.run` retains the exact
Host-bound Scanner behavior. `planning.create(request, context)` is a
reserved fail-closed entrypoint pending trusted operation integration.

**Review:** `review/gap_analysis.py` is the canonical implementation.
The previous `checks/gap_analysis.py` module was removed after consumers
were migrated to `review/gap_analysis.py`.

**Fixtures:** `agent.skills.planner.fixtures.prepare` only copies declared
fixture specifications into drafts; it does not test, certify or approve them.

**Boundary:** Planner owns candidate design, not authorization, trusted
receipts, Host transitions, sandbox execution, or independent acceptance.
