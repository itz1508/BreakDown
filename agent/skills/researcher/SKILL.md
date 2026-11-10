# Researcher — sourced evidence investigation

**Mini-pipeline:** `research.yaml` now contains the original `review`, `retrieve`, and `main` segments. The former `search.yaml` declarations were moved without registering new executable search operations.

**Python:** `researching.run(context, envelope, arguments)` preserves the original Host-managed Research delegation and state-root consistency check.

**Searching:** No standalone `searching.py` implementation exists in the repository. Declared retrieval operation IDs remain unbound. Do not fabricate network/search behavior or bypass Host tool authorization.

**Shared Catalog:** Templates remain at `agent/catalog/` for Auditor PRE and Researcher; matching synthetic examples is not verification evidence.

**Boundary:** No independent stage transitions, architectural decisions, approvals, effects or trusted receipts.
