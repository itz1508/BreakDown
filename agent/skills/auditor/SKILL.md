# Auditor — read-only repository inspection

**Executable:** `agent.skills.auditor.audit.run(context, envelope, AuditArguments)`.

**Input:** Host-persisted audit-discovery dispatch, Runtime workspace root, requested capabilities and bounded scope. Existing persisted role ID `audit_discovery` is preserved.

**Checks (fixed order):** paths, contracts, dependencies, security, completeness, wiring, frontend, integration, state, recovery, verification. The CLI and Host use the same `CAPABILITY_ORDER` and fail closed on unreadable or symlinked sources.

**CodeDesign preparation:** After repository inspection, requirement assessment and findings—and before Planning, `agent.skills.auditor.code_design.review_questions` supplies evidence questions for existing CodeDesign candidate origins. Audit Discovery records source-grounded candidates and unknowns; it does not choose an implementation design or modify application source.

**Output:** Source-grounded `AuditResult` with findings and limitations. Candidate CodeDesign requirements remain informational until Planner review. No repository edits, approved Build actions, trusted receipts, or stage transitions.

**Boundary:** The standalone CLI and MVP Audit capability return static `AuditResult` / `AuditFindingsRecord`, not the full Research-bound `AuditDiscoveryPackage`. Source entry/exit checkpoints, requirement assessments, CodeDesign candidate publication and stage transition are Host-owned and cannot be inferred from a static scan.

**Runtime:** `system.host.skill_dispatch.execute_skill` validates persisted routing before loading this role. References: `references/audit_guidance.md`.
