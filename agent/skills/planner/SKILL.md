# Planner — candidate planning and evidence review

**Mini-pipeline:** `plan.yaml#main` traces requirements, inspects patterns,
drafts a candidate before scanning, records findings, and prepares
unverified fixture drafts. No approval or freeze operation is defined.

**Python API:** `agent.skills.planner.planning.run` retains the exact
Host-bound Scanner behavior. `planning.create(request, context)` is a
reserved fail-closed entrypoint pending trusted operation integration.

**Tools** (leading underscore = internal module, CPython convention):

- `tools/_gap_analysis.py` — canonical missing-capability and structural gap
  analysis. The previous `checks/gap_analysis.py` module was removed after
  consumers were migrated.
- `tools/_create_task_todo.py` — creates TaskTodo drafts from
  BuildSpecification actions (CPython `makefreeze` pattern: iterate sorted
  input, produce structured output per item). No persistence, no Host dispatch.
- `tools/_create_plan.py` — orchestrates sub-tools to assemble a
  CandidateSpecification draft (CPython `freeze` pattern: coordinate
  `_create_task_todo` and gap analysis in sequence). No publication.
- `../tools/repo_scan.py` — passive repository-structure observation
  (CPython `_files` pattern: declarative checks, path validation). Returns a
  dict of 7 booleans; never modifies the working tree.

**Boundary:** Planner owns candidate design, not authorization, trusted
receipts, Host transitions, sandbox execution, or independent acceptance.
