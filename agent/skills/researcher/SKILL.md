# Researcher — sourced evidence investigation

**Mini-pipelines:** `research.yaml#main` defines investigation order;
`search.yaml#review` prepares bounded retrieval questions before Research;
`search.yaml#retrieve` describes compound retrieval and source expansion.

**Python:** `research.run(context, envelope, arguments)` retains the
existing Host-provided service; these YAML files do not activate that service.

**Shared Catalog:** Templates and examples remain at `agent/catalog/`
for Auditor PRE and Researcher. Template matches are not evidence.

**Boundary:** No independent stage transitions, architectural decisions,
approval, effects, or trusted receipts. Search operation IDs are unbound.
