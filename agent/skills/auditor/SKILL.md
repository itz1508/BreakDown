# Auditor — repository context and source inspection

**Executable:** `agent.skills.auditor.auditing.run(context, envelope, AuditArguments)`.

**Declarative intake:** `audit.yaml#pre` declares scoped intake and Research-question preparation; its operations are unbound, and Host routing for the legacy `audit_discovery` identity is unchanged.

**Current executable:** `auditing.run(context, envelope, arguments)` still delegates to the existing read-only source inspection registry. It is registered through the legacy `audit_discovery` Host identity. **It is not yet an implementation of Auditor PRE**, and no Host routing has been changed.

**Tools (fixed order):** paths, contracts, dependencies, security, completeness, wiring, frontend, integration, state, recovery. The CLI and Host use the same `CAPABILITY_ORDER` and fail closed on unreadable or symlinked sources. Verification comparison belongs to `agent.skills.tools.verify_all`.

**CodeDesign:** The evidence-question capability is the separate `agent.skills.coder` skill, positioned after Research and before Planning. Auditor no longer owns its Python implementation. Audit Discovery records source-grounded candidates and unknowns; it does not choose an implementation design or modify application source.

**Shared Catalog:** `agent/catalog/research_samples.yaml` contains synthetic guidance, not verified source evidence.

**Boundary:** No Planner decisions, project-source mutations, approvals, independent verification or trusted receipts. Read `references/audit_guidance.md` for known static inspection limitations.
