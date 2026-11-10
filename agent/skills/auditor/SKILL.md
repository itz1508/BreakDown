# Auditor — repository context and source inspection

**Target position:** Auditor PRE before Research. `audit.yaml#pre` declares scoped intake and Research-question preparation; its operations are **unbound**.

**Current executable:** `auditing.run(context, envelope, arguments)` still delegates to the existing read-only source inspection registry. It is registered through the legacy `audit_discovery` Host identity. **It is not yet an implementation of Auditor PRE**, and no Host routing has been changed.

**CodeDesign:** The evidence-question capability is now the separate `agent.skills.code_design` skill after Research and before Planning. Auditor no longer owns its Python implementation. Existing AuditDiscovery/CodeIntent wire contracts remain unchanged pending an independently approved migration.

**Shared Catalog:** `agent/catalog/research_samples.yaml` contains synthetic guidance, not verified source evidence.

**Boundary:** No Planner decisions, project-source mutations, approvals, independent verification or trusted receipts. Read `references/audit_guidance.md` for known static inspection limitations.
