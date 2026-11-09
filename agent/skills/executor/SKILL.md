# Executor — isolated Sandbox and source-file execution

**Owner:** Agent-side isolated execution implementation and its source-file staging; **not** a workflow transition owner or an authority issuer.

**Canonical package:** `agent/skills/executor/sandbox_v3/`, containing the standalone `modal_build_sandbox` project, pinned `uv.lock`, tests, and offline/connected validation scripts. This is the single implementation of source snapshot handling, allowed-path patch application, Sandbox lifecycle, evidence export, and attempt reconciliation.

**Inputs:** A Host-admitted, pinned `SandboxExecutionRequest` (snapshot, candidate bundle, approved paths/preimages, image and profile identities, bounded checks, and attempt identity). The Sandbox request validates shape and data coherence; **it is not an authorization token**.

**Execution:** The existing Host verifies immutable approval and Build Admission before provisioning the Sandbox. The standalone runner checks hashes, paths and command plans; the isolated Ubuntu/Python image is selected by a trusted Host, not by an agent proposal. No secret, volume, OIDC, network or authoritative checkout is supplied to the Sandbox. The current implementation executes a patch-first runner, **not an autonomous coding agent inside the Sandbox**.

**Outputs:** `result.json`, `after.tar`, `evidence.zip`, durable attempt state. Host independently checks exports and decides Build Validation, CAS promotion and receipts.

**Out of scope (unchanged owners):** `agent/runtime/artifact_store.py`, authorization, checkpoint/receipt/event stores, Build Admission, Host dispatch and authoritative source promotion. `agent/skills/builder` remains the admitted Build role; this Executor is **not** an additional workflow stage or independently dispatchable role.

**Standalone validation:** `cd agent/skills/executor/sandbox_v3 && uv sync --locked --extra modal --group dev && uv run --no-sync pytest -q tests --ignore=tests/integration`.

**Integration status:** No Host-to-Modal Sandbox E2E receipt or production Build authorization is implied by this structural move. Do not register a second builder or claim authorization from skill documentation.
