# Coder â€” CodeDesign evidence questions after Research

**Role:** A standalone post-Research CodeDesign capability, before Planner. "Coder" here names evidence-driven code-design review; it is **not Builder** and does not write project source.

**Implementation:** `coding.review_questions(candidate)` is the original pure function from CodeDesign. The function's question ordering, intent-origin keys, and error behavior are unchanged.

**Pipeline:** `code.yaml#main` declares the unbound `code_design.review_questions` operation. Its operation identifier is intentionally unchanged to avoid renaming an existing rule identity as a side effect of package naming.

**Contract identity:** Keep `agent.skills.auditor.contracts.code_design.CodeDesign`, `AuditDiscoveryPackage.code_intents`, and CodeDesign review wire fields unchanged. Moving typed contracts or exposing a new Host stage requires separate evidence and approval.

**Missing implementation:** Research-to-repository correlation, full candidate production and independent assignment are not provided by the current function.

**Boundary:** No source writes, stage transitions, approval, final architecture selection, trusted receipts or Builder execution.
