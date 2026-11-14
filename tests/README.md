# Test suite

Two layers only. Everything else was removed: a large unit/contract layer that
restated model defaults did not protect the workflow, and on a machine with a
restricted `%TEMP%` it failed before it could assert anything.

## `tests/e2e` — connected workflow tests

These drive the same objects the runtime uses: `HostController`, the artifact,
receipt, checkpoint and event stores, the scanner gateway, build admission and
the effect executor, plus the CLI entrypoints. A stage is never reported complete
unless the host accepted persisted evidence, a bound receipt and host-assigned
work. Files are written to a real workspace and verified independently.

| File | Proves |
| --- | --- |
| `test_workflow_lifecycle.py` | Six stages advance in order, only with host-assigned completed work, and durable state survives a fresh `HostController`. Dispatch routing and returns are exact. |
| `test_trust_boundaries.py` | Forged and unbound receipts fail, completed work needs real evidence, artifact revisions are immutable, filesystem authority is rooted. |
| `test_build_and_verify.py` | A compiled TaskTodo is admitted, executed as real effects, and the produced program is verified by an independent subprocess. |
| `test_cli_contract.py` | `skills`, `status`, `resume`, `verify` and `scan` run against real state; `skills` is checked as a subprocess. |
| `test_scanner_checks.py` | The host scanner persists a verified pass with a bound receipt, orders its events, and rejects a forged receipt. |
| `test_spec_search.py` | Spec Search ranks a declaration above prose, digests its snippets, reports truncation and skipped files, and refuses scope escape. |
| `test_researcher_search.py` | The Researcher loop calls the real local tools, rejects unknown tools and escaping reads, distinguishes truncated/pending/exhausted/failed, and persists audit, code and fixture artifacts. |
| `test_research_lifecycle.py` | The Research case lifecycle admits, produces, reviews and hands off with host receipts, plus adversarial cases. |
| `test_audit_readonly.py` | The audit role runs through a persisted dispatch envelope without changing bytes and refuses scope escape. |

Fixtures in `tests/fixtures` supply *upstream inputs* only (a planning record, a
structural-gap receipt, a task-todo specification). They never claim that a
stage ran.

## `tests/quality` — gates and measurements

| File | Purpose |
| --- | --- |
| `test_skill_definitions.py` | Role definitions are owned, closed, dependency-ordered and cannot self-authorize; the stage-to-role table is exact. |
| `test_layering.py` | Contracts do not import runtime modules, validation does not perform IO, the retired-path policy holds, and every e2e module is marked and mock-free. |
| `test_configuration.py` | The shipped provider YAML loads, environment overrides resolve, a missing key fails closed, and the factory builds an adapter offline. |
| `benchmark_decision_trace.py` | Scanner cache equivalence and timing against the legacy validator oracle (stdout JSON, CI measured). |
| `evaluate_gap_sklearn.py` | Labeled offline gap evaluation scored by scikit-learn; observations come from the real `ScannerGateway`. |

## Prerequisites and cost

No network access, API key, model call or container is required. Everything runs
against a disposable state root and a temporary workspace, in seconds, on Python
3.11 and 3.12. The only substituted inputs are the planning record, the
structural-gap receipt and the synthetic scanner checks, all stored under
`tests/fixtures`.

## Running

```sh
uv run --no-sync pytest -q            # everything
uv run --no-sync pytest -q -m e2e     # connected tests only
uv run --no-sync pytest -q tests/quality
uv run --no-sync pytest -q tests/e2e/test_workflow_lifecycle.py
```

`addopts` sets `--basetemp=.pytest-tmp` so temporary state never depends on
`%TEMP%` permissions. The directory is git-ignored.

## Rules for new tests

1. Only add a test that asserts an outcome a user or CI could observe: persisted
   state, exit codes, files on disk, stream events.
2. Do not mock the system under test. Stub only upstream inputs that the host
   itself cannot produce in a unit-run (for example the structural-gap receipt).
3. Prefer extending one of the existing end-to-end scenarios over adding a new
   file that re-tests a model field.
4. Every e2e module sets `pytestmark = pytest.mark.e2e`.
