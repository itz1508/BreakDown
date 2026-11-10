# CodeDesign — evidence questions after Research

**Position:** Auditor PRE → Researcher → CodeDesign → Planner (declarative target, not activated Host routing).

**Implementation:** `code_design.review_questions(candidate)` is the existing pure function moved from Auditor. It returns questions keyed by the candidate's `intent_origin`, with explicit evidence requirements and unresolved concerns.

**Contract identity:** The existing `contracts.workflow.auditor.code_design.CodeDesign` and `AuditDiscoveryPackage.code_intents` definitions are preserved. This move does **not** authorize persisted schema or receipt changes.

**Declared mini-pipeline:** `code_design.yaml#main` is inactive and its operation remains unbound. Research-to-repository correlation, candidate production, trusted assignment and new Host transitions are **not implemented**.

**Boundary:** CodeDesign does not perform Research, approve requirements, choose architecture, implement source changes, issue receipts or conduct independent verification. Planner owns final design decisions.
