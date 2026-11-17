# Planner — gap resolution, specification and approval preparation

**Workflow ownership:** `planning`. Planner executes PP3,
`planner_processing_plan`, created by Auditor at the end of
`audit_post_research`.

**Ordered substeps:**
1. `create_gap_processing_design`
2. `gap_resolution`
3. `scan_verify_chaos` — Planner paper-exercise/self-review, not independent verification
4. `create_task_todo`
5. `checkpoint_freeze_state` — Runtime-owned
6. `freeze_and_hash`
7. `preflight_check`
8. `decision_point_user_confirmation` — Runtime routes the explicit user decision
9. `confirm_plan` — Runtime binds the approved revision and source checkpoint, then PP4 is created

**Canonical TaskTodo:** `requirement_spec.implementation_steps` is the sole
canonical task list. Do not create a parallel `builder_processing_steps`,
`phase_steps`, wave schedule or second task artifact. Each task describes its
target, expected outcome and acceptance checks.

**Open questions:** Resolve them from available evidence or preserve them in
`open_questions`; do not silently fill unknowns with guesses.

**Current implementation boundary:** The current `planning.create()` entrypoint
is fail-closed and reports that no trusted planning executor is installed.
The v6 planning sequence is declarative until that integration exists.
