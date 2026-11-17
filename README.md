# BreakDown v6

BreakDown defines an evidence-oriented workflow for turning a user request into
a reviewed, bounded implementation plan and a recorded execution outcome.

## Canonical workflow

The only canonical workflow definition is
[`agents/breakdown.yaml`](agents/breakdown.yaml), version 6.

[Open the workflow diagram](docs/workflow.html).

| Order | Stage | Owner | Processing plan |
|---:|---|---|---|
| 1 | `audit_pre_research` | Auditor | PP1 — created by Runtime |
| 2 | `gate_1` | User | Decision only; not a plan input |
| 3 | `research` | Researcher | PP2 — created by Auditor |
| 4 | `audit_post_research` | Auditor (Coder sub-role) | Creates PP3; does not execute it |
| 5 | `planning` | Planner | PP3 — creates PP4 after confirmation |
| 6 | `builder` | Builder | PP4 — sequential execution |
| 7 | `completion` | Runtime | Records actual terminal outcome |

Every user request creates PP1 before the first stage. Each later phase consumes
the exact processing-plan handoff created by the preceding phase. YAML describes
stages, ownership, transitions, schemas and artifact flow; runtime owns plan
instances, decisions, status, hashes, timeouts, persistence and recovery.

## Processing plans and specification

The four processing plans are PP1 `input_processing_plan`, PP2
`researcher_processing_plan`, PP3 `planner_processing_plan`, and PP4
`builder_processing_plan`. Their shared authored shape and separate runtime
record shape are defined in
[`processing_plans.schema.json`](agents/skills/shared/contracts/workflow/processing_plans.schema.json).

The Planner's strict requirement specification is defined in
[`requirement_spec.schema.json`](agents/skills/planner/contracts/requirement_spec.schema.json).
Its `implementation_steps` field is the one canonical TaskTodo list. There is
no parallel builder task-list field, phase-step artifact or dependency-wave
schedule.

Research remains citation-capable plain output. Structured JSON schemas are
used for the requirement specification and processing-plan records, not to
discard Research citations.

## Ownership boundaries

- **Auditor:** read-only repository discovery and post-Research evidence reconciliation.
- **Coder:** Auditor sub-role during `audit_post_research`; prepares coding inputs and does not change source.
- **Researcher:** sourced technical investigation and fixture generation when evidence supports it.
- **Planner:** gap design, gap resolution, paper-exercise/self-review, requirement specification, hashing and preflight preparation.
- **Builder:** approved sequential sandbox execution and result synchronization.
- **Runtime:** owns plan records, checkpoints, confirmation routing, limits, recovery and completion records.
- **User:** makes the explicit decisions at `gate_1` and plan confirmation.

Planner's `scan_verify_chaos` is a self-review exercise. It is not an independent
verification stage. No separate verifier stage is declared.

## Execution rules

Builder executes `implementation_steps` sequentially. Each task follows
`apply → check → record`; Builder stops on the first `not_valid` task.
Builder-only limits are two corrections per task and one attempt. Corrections
remain inside the sandbox and task target. Partial results are retained as
evidence and are not synchronized to application source unless every task is
completed and no scope or authorization gate was violated.

Evaluated results use `valid`, `not_valid` or `uncertainty`. Execution states
use `completed`, `failed`, `blocked`, `not_run` or `skipped`. Uncertainty
does not advance a stage or gate.

## Current implementation boundary

This v6 branch changes the declarative workflow, schemas, role guidance,
stage-tool mapping, documentation and workflow tests. It does **not** install a
new workflow-transition runtime.

The current `agents.system.coordinate()` path processes an individual
`TaskTodo` immediately; the current Planner entrypoint is fail-closed until a
trusted planning executor is installed. The role skill YAML operations remain
unbound declarations. The existing Builder Python implementation is not yet
the v6 sequential PP4 executor. Therefore v6 describes the target workflow
contract; it must not be represented as an already operational end-to-end
workflow.

## Verification

From the repository root:

```sh
uv run --no-sync pytest tests/test_workflows.py tests/quality/test_skill_definitions.py -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy agents
uv run --no-sync pytest -q
```

Tests establish the static contract and repository behavior they actually
exercise. They do not prove an end-to-end v6 run or Builder sandbox behavior.
