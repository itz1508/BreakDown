# OneShot Sandbox — provider-neutral isolated executor

**Location:** `agent/skills/executor/sandbox/`. This is the single implementation of disposable execution, source staging, bounded patch application, checks, evidence export, and attempt reconciliation.

## Architecture

```text
Host (approval + Build Admission + exact source/image/profile)
    |
    v
SandboxExecutionRequest (immutable validated data; NOT permission)
    |
    v
StandaloneRunner / SandboxBackend Protocol
    +-- source snapshots / patch / checks / allowed paths / evidence
    +-- attempt store / pre-effect reconciliation
    |
    +-- integrations/modal.py  [optional, explicitly selected]
    +-- further integrations   [not implemented]
    |
    v
Host independent evidence verification and source promotion
```

`oneshot_sandbox/` is the core Python package. It contains no required Modal SDK dependency and does not select Modal implicitly. Backends implement the `SandboxBackend` protocol in `backend.py`. `integrations/` contains an allowlisted registry and the optional Modal adapter. An unknown backend is rejected before loading any provider.

The generic runner does not grant execution authority. Before invoking it, the trusted Host must verify the exact approval, Build Admission, source identity, permitted files, command/tool profile, immutable image, and attempt identity. The local `profile_digest` validates data coherence only; it cannot substitute for a trusted Host receipt.

## Source and execution boundaries

- Core: `contracts.py`, `backend.py`, `snapshot.py`, `applicator.py`, `policy.py`, `evidence.py`, `recovery.py`, `runner.py`.
- Modal-only integration: `integrations/modal.py`. It selects an existing Modal App and a **Host-pinned** image ID; it enforces no network, no secrets, no volumes, no OIDC, no GPU, no exposed ports, and bounded CPU/RAM/lifetime. Other backends must implement equivalent approved isolation constraints.
- No authoritative checkout or production credentials are transferred to the sandbox. The candidate patch and JSON manifest carry no permission.
- The current worker executes an approved **patch-first** workflow. It does not create or run an autonomous coding agent.
- An interrupted attempt remains uncertain until reconciliation. Never blindly retry an uncertain effect or promote sandbox output directly.

## Local checks

```sh
cd agent/skills/executor/sandbox
uv lock --check
uv sync --locked --group dev
uv run --no-sync python -m compileall -q src scripts tests
uv run --no-sync ruff check src tests scripts
uv run --no-sync ruff format --check src tests scripts
uv run --no-sync mypy src
uv run --no-sync pytest -q tests --ignore=tests/integration
```

Offline validation requires no provider credentials:

```sh
uv run --no-sync oneshot-sandbox validate ./request.json
```

## Optional Modal backend

```sh
uv sync --locked --group dev --extra modal
oneshot-sandbox execute ./request.json --backend modal --app EXISTING_MODAL_APP
```

A Modal App and prebuilt immutable image ID must already exist; `--create-app` is an explicit opt-in, not a default. The CLI checks the required `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` values without printing them. An unknown backend is denied rather than dynamically imported from user input.

For an explicitly approved connected Modal GOOD/BAD test, provide `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `ONESHOT_MODAL_IMAGE_ID`, and `ONESHOT_MODAL_APP_NAME`, then run:

```sh
RUN_MODAL_E2E=1 uv run --no-sync pytest -q tests/integration/test_modal_e2e.py
```

## Output / integration status

`result.json`, `after.tar`, `evidence.zip`, and durable attempt state are exported. The trusted Host must independently verify before issuing trusted receipts, CAS promotion, or final E2E status.

This remains a **standalone Sandbox capability**; no connected OneShot Host-to-Sandbox admission, deployment, or production E2E is claimed from its unit tests.
