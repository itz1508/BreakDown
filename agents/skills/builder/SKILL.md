# Builder — sequential execution of the confirmed specification

**Workflow ownership:** `builder`. Builder executes PP4,
`builder_processing_plan`, created by Planner only after Runtime completes
`confirm_plan`.

**Execution order:** Verify the frozen content hash, verify approved source
identity, enter the authorized sandbox, execute
`requirement_spec.implementation_steps` sequentially, synchronize eligible
results, then exit the sandbox.

**Per-task pattern:** `apply → check → record`. Stop on the first `not_valid`
task. Later tasks remain `not_run`.

**Correction and retry limits:** Maximum two Builder-only corrections per task,
inside the sandbox, and one Builder attempt. Corrections must remain within the
task target, restore the task-start checkpoint first, and address a different
new error. Stop on scope violation, missing target, unmet criterion or invalid
check. Never extend a time or cost limit.

**Synchronization:** Apply results to application source only when every task
is completed and no scope or authorization gate was violated. Otherwise retain
partial results as evidence; do not apply them to application source.

**Current implementation boundary:** The existing Python Builder contains a
legacy execution surface and is not the v6 sequential workflow executor.
The YAML and this guidance specify the target contract; they do not establish
that PP4 verification, correction caps, synchronization gates or sandbox
lifecycle are enforced by the current runtime.
