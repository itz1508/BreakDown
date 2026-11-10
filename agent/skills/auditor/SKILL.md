# Auditor — source-grounded PRE and POST review

**Mini-pipeline:** `audit.yaml#pre` prepares scoped research questions, and
`audit.yaml#post` inspects repository evidence and consolidates findings.
These are Agent-side process segments, not new Host stages. The existing
persisted `audit_discovery` identity remains unchanged.

**Python:** `audit.run(context, envelope, arguments)` retains the existing
ordered, read-only check registry and the external Host dispatch boundary.

**Shared Catalog:** Both Auditor PRE and Researcher can consult
`agent/catalog/research_samples.yaml`. Its templates are synthetic guidance,
not findings or verification evidence.

**Boundary:** Auditor returns source-grounded findings and unknowns. It may
not choose Planner designs, write application source, issue Host receipts or
authorize Builder effects. Guidance: `references/audit_guidance.md` and
`agent/skills/references/aggregation_patterns.md`.
