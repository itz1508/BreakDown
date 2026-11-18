# Auditor — pre- and post-Research repository evidence

**Workflow ownership:** `audit_pre_research` and `audit_post_research`. Both are
read-only with respect to application source.

**PP1 / pre-Research.** Runtime creates the input processing plan after the
user request. Auditor executes PP1, preserves original intent, inventories
relevant scaffolding, defines file specifications and research items, captures
the source checkpoint, and creates PP2 for Research.

**PP3 preparation / post-Research.** Auditor reconciles Research findings with
actual repository source, classifies and normalizes evidence, preserves
unresolved questions, and creates the coding processing design, coding plan,
coding steps and PP3 for Planner. This stage creates PP3; it does not execute it.

**Coder sub-role.** The Coder capability is invoked only as an Auditor sub-role
during `audit_post_research`. It prepares evidence-grounded coding inputs. It
does not own a workflow stage, make final architecture decisions, modify
application source, authorize execution or advance workflow state. See
`agents/skills/coder/SKILL.md`.

**Current implementation boundary.** The current Python Auditor returns
source-grounded scan results. The workflow's PP1/PP3 creation and stage handoffs
are declarative requirements; no claim is made that a stage-transition runtime
executes them today.

**Tools and references.** Existing fixed-order, read-only scan capabilities
remain the implementation evidence. A declared operation is not proof that an
adapter or transition is installed.
