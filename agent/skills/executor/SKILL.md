# Executor — isolated sandbox execution and workspace file handling

**Role:** Execution capability assigned by the existing Host; not a workflow stage, admission authority, receipt issuer, or new Builder.

**Canonical implementation:** `agent/skills/executor/sandbox/` owns source-snapshot verification, sandbox-local file staging, patch application, bounded command execution, changed-path inspection, evidence export, and attempt-state reconciliation.

**Contracts and ownership:** Host retains workflow dispatch, source identity, approval, Build Admission, authoritative ArtifactStore, checkpoints, receipts, tool allowlists, and CAS promotion. `agent/skills/builder/` remains the Build role. A Sandbox request describes input only and does not confer authorization.

**Backends:** Provider-neutral `oneshot_sandbox` core defines the execution-backend interface. Integrations live under `oneshot_sandbox/integrations/`; the Modal adapter is optional and selected explicitly by trusted configuration. No provider credentials or SDK imports are required for offline validation.

**Isolation:** Runtime must enforce the admitted image/profile, resource limits, network and secret policy, preimages, and permitted paths before creating effects. The current backend is patch-first, not an autonomous coding agent inside the sandbox.

**Outputs:** `result.json`, `after.tar`, `evidence.zip`, durable per-attempt state. Host independently verifies and reconciles outputs before considering source promotion.

**Validation:** `cd agent/skills/executor/sandbox && uv sync --locked --group dev && uv run --no-sync pytest -q tests --ignore=tests/integration`. Connected Modal E2E requires explicit opt-in and credentials. Neither local tests nor this relocation establish integrated Host admission or real Sandbox E2E.
