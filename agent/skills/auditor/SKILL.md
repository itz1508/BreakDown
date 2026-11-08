# Auditor — read-only repository inspection

**Executable:** `agent.skills.auditor.run.run(context, envelope, AuditArguments)`.

**Input:** Host-persisted audit-discovery dispatch, Runtime workspace root, requested capabilities and bounded scope. Existing persisted role ID `audit_discovery` is preserved.

**Checks:** Migrated `checks/` implementations: paths, wiring, security, contracts, completeness, verification, frontend, state, dependencies, integration, recovery.

**Output:** Source-grounded `AuditResult` with findings and limitations. Candidate CodeDesign requirements are informational until Planner review. No repository edits, approved Build actions, trusted receipts, or stage transitions.

**Runtime:** `agent.runtime.skill_dispatch.execute_skill` validates the persisted route before loading this role. References: `references/audit_guidance.md`.
