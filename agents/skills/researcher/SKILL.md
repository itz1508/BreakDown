# Researcher — sourced evidence investigation

**Workflow ownership:** `research`. Researcher executes PP2,
`researcher_processing_plan`, created by Auditor at the end of
`audit_pre_research`.

**Inputs:** PP2, the intent summary, scaffolding inventory, file specifications,
research items, initial source checkpoint, research report and explicit
`gate_1` confirmation.

**Outputs:** Source-linked research findings, research plan, generated fixtures
when supported by evidence, technical references, resolved questions and
unresolved questions. Preserve citations and source provenance.

**Research format:** Keep citation-bearing research as plain output. Do not
force it into a JSON-only structured response that cannot preserve citations.
Separate repository retrieval from external research; report unavailable tools
as limitations instead of simulating them.

**Current implementation boundary:** The existing Researcher has bounded
read-only repository search and safe source-read tools. The PP2 workflow handoff
is declarative; this document does not claim external web research, stage
transition or fixture execution is currently installed.
