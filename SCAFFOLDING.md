# SCAFFOLDING — `agents/` and `system/` inventory

Generated: 2026-11-15 · Repository snapshot: `61790f0c3aad330ba67f068d36171c5b838289bd` (worktree contains the unverified storage-ownership migration: `agents/shared/base.py` added, `skills/shared/contracts/workflow/common.py` deleted, 26 files rewired).

Every file under `agents/` and `system/` (excluding `__pycache__/` and the third-party `.agents/` Modal reference library), with a short description and role classification.

**Role legend**

- `HOST` — runtime / control-plane, not a workflow role
- `SHARED` — cross-role infrastructure
- `AUDITOR`, `BUILDER`, `CODER`, `PLANNER`, `RESEARCHER`, `SPEC_SEARCH` — workflow roles
- `—` — packaging marker / empty placeholder

---

## 1. Workflow control plane

| File | Description | Role |
|---|---|---|
| `agents/breakdown.yaml` | The single workflow definition: 9 stages (user_input → prepare_request → specification_review → specification_check → research → repository_audit → … → build → completion), ownership, handoffs, change-handling rules | HOST |
| `agents/__init__.py` | Package marker for the `agents` distribution package | — |
| `agents/__main__.py` | `python -m agents` prints usage to stderr and exits 2 — no direct action | — |
| `agents/system/__init__.py` | Package marker | — |
| `agents/system/_call.py` | Allow-list of approved `(skill, action)` pairs → fixed `python -m agents.skills.<role>` argv; unknown pairs fail closed with `UnknownSkillActionError` | HOST dispatch |
| `agents/system/_coordinate.py` | Saves a `TaskTodo` + `todo_created` event, delegates immediately, returns the terminal `ExecTodo`. No scheduler, batching, wave management or polling | HOST runtime |
| `agents/system/_delegating.py` | One todo → one subprocess; parses the last JSON line of stdout; persists terminal `ExecTodo` + event on every path (completed / failed / timed_out / cancelled) | HOST runtime |
| `agents/system/_runtime.py` | Asyncio subprocess runner: JSON payload → stdin, concurrent pipe drain (deadlock-free), timeout → terminate → kill after 5 s grace; partial output returned with `timed_out=True` | HOST runtime |

## 2. Cross-role shared infrastructure

| File | Description | Role |
|---|---|---|
| `agents/shared/__init__.py` | Package marker | — |
| `agents/shared/io.py` | Stdin/stdout JSON envelope for every skill process: `Request`/`Response` models, `read_request`/`write_response`/`ok_response`/`error_response`; exit code carries success | HOST↔role boundary |
| `agents/shared/base.py` | `ContractModel`, `ArtifactRef`, `Sha256`, `StepResult`, `OperationState`, `DiagnosticStatus` + typed ID aliases — single copy of the shared primitives (relocated verbatim from the deleted `skills/shared/contracts/workflow/common.py`) | SHARED primitives |
| `agents/tools/base.py` | `Tool` base class + provider-neutral `declaration()`; `resolve_scoped` refuses paths outside the configured root | SHARED tool surface |
| `agents/tools/file_tools.py` | Bounded file read/list (write/edit variants) under a scoped root | SHARED (read used by researcher) |
| `agents/tools/search.py` | `RepositorySearchTool`: literal-term search returning path/line/snippet, bounded results | SHARED (used by researcher) |
| `agents/tools/server.py` | `ServerTool`: provider-executed capabilities (e.g. `web_search`, `code_execution`) — declared here, executed by the provider; no client-side `execute` | SHARED / provider adapter |
| `agents/tools/think.py` | Reasoning scratchpad — records a thought and returns it; zero external effects | SHARED |

## 3. Roles — `agents/skills/`

### 3.1 auditor — read-only repository inspection

| File | Description | Role |
|---|---|---|
| `auditor/SKILL.md` | Role instructions: fixed check order, boundaries (no edits, no receipts, no stage transitions) | AUDITOR |
| `auditor/audit.yaml` | Declarative mini-pipeline (`inspect_request` → `identify_search_questions`), all steps `unbound`, read-only policy | AUDITOR |
| `auditor/__init__.py` | Package marker | — |
| `auditor/__main__.py` | stdin-envelope CLI adapter calling the audit execution | AUDITOR |
| `auditor/auditing.py` | `run()`: executes the ordered capability scan over the workspace, returns `AuditResult` without receipts or source modification | AUDITOR |
| `auditor/references/audit_guidance.md` | Capability guidance: intake, ordered inspection, capability-module map | AUDITOR |
| `auditor/contracts/_discovery.py` | `AuditDiscoveryPackage`, `CodeDesign`, finding/disposition models (consumed cross-role by coder, planner, shared validation) | AUDITOR |
| `auditor/contracts/_report.py` | Audit report models | AUDITOR |
| `auditor/contracts/code_design.py` | Bridge re-export: discovery models + planner `CodeDesignReview`/`IntentDisposition` | AUDITOR |
| `auditor/contracts/validation.py` | Validation for audit discovery packages | AUDITOR |
| `auditor/tools/core.py` | `Finding`/`evidence` helpers, `safe_read_bytes`/`safe_read_text` (reused by researcher), `scan()` dispatch to all capability scanners | AUDITOR (read primitives SHARED) |
| `auditor/tools/completeness.py` | AST scan for `NotImplementedError` stubs | AUDITOR |
| `auditor/tools/contracts.py` | Verifies literal internal import targets exist, without importing project modules | AUDITOR |
| `auditor/tools/dependencies.py` | Frontend manifest ↔ lockfile reproducibility check | AUDITOR |
| `auditor/tools/frontend.py` | Research endpoint / artifact-viewer / status wiring gaps | AUDITOR |
| `auditor/tools/integration.py` | Integration-surface checks | AUDITOR |
| `auditor/tools/paths.py` | Symlink containment + broken-symlink findings | AUDITOR |
| `auditor/tools/recovery.py` | Recovery-path checks | AUDITOR |
| `auditor/tools/security.py` | `subprocess`/`os.system`/`shell=True` candidates — review flags, not exploit proofs | AUDITOR |
| `auditor/tools/state.py` | Static audit of host receipt identity binding in `agent/runtime/controller.py` | AUDITOR |
| `auditor/tools/wiring.py` | Literal frontend fetch ↔ FastAPI route cross-check (dynamic routes not classified as broken) | AUDITOR |

### 3.2 builder — effect execution under host authorization

| File | Description | Role |
|---|---|---|
| `builder/SKILL.md` | Preparation-only contract; the real executable path is host-authorized `building.run` | BUILDER |
| `builder/build.yaml` | Mini-pipeline: receive candidate → prepare external handoff; no effects, no approval | BUILDER |
| `builder/__init__.py` | Package marker | — |
| `builder/__main__.py` | stdin-envelope CLI calling `building.execute_admitted` | BUILDER |
| `builder/building.py` | Constructs the `EffectExecutor` (AuthorizationEngine over workspace+state roots, artifact/checkpoint/receipt stores) and delegates admitted actions | BUILDER |
| `builder/build_admission.py` | Host-owned admission gate: frozen-spec digest verify, pinned tool-registry load, `tool_invocation_gaps`, admission receipts | BUILDER |
| `builder/build_todos.py` | Deterministic frozen-Plan → `TaskTodo` compilation (no effects) | BUILDER |
| `builder/effect_executor.py` | Sole producer of physical effects: atomic write/move/remove with realpath containment, checkpoints, operation receipts | BUILDER |
| `builder/package_lock.py` | Binds research/audit/frozen-spec/fixture digests; any drift invalidates the lock | BUILDER |
| `builder/contracts/build.py` | `BuildActionStatus`, `BuildActionExecution` | BUILDER |
| `builder/contracts/schedule.py` | `BuildTask`/`BuildBatch`/`BuildWave`/`VerifiedWaveResult` over admitted todos | BUILDER |

### 3.3 coder — CodeDesign evidence questions (explicitly *not* Builder)

| File | Description | Role |
|---|---|---|
| `coder/SKILL.md` | Role instructions: post-Research evidence questions; no source writes, no design selection | CODER |
| `coder/code.yaml` | Mini-pipeline declaring `code_design.review_questions` (unbound) | CODER |
| `coder/__init__.py` | Package marker | — |
| `coder/__main__.py` | stdin-envelope CLI | CODER |
| `coder/coding.py` | `review_questions(design)` — the original pure question-generation function | CODER |
| `coder/code.py` | argparse CLI: CodeDesign JSON file → evidence questions | CODER |

### 3.4 planner — candidate planning + gap analysis

| File | Description | Role |
|---|---|---|
| `planner/SKILL.md` | Role instructions: candidate design only; no approval, freeze, or receipts | PLANNER |
| `planner/plan.yaml` | 7-step candidate pipeline (trace → inspect → draft → scan → findings → fixtures → return); ⚠ references nonexistent `contracts/scanner.py` | PLANNER |
| `planner/__init__.py` | Package marker | — |
| `planner/__main__.py` | stdin-envelope CLI adapter | PLANNER |
| `planner/planning.py` | `create()` fails closed with `PlanningPipelineNotActive` — declarative only | PLANNER |
| `planner/host_gap_analyzer.py` | Host boundary: verifies immutable inputs, runs the trusted analyzer, persists result, issues completion receipt | PLANNER |
| `planner/tools/gap_analysis.py` | Canonical pure structural-gap analysis (workflow concern matrix, walking-skeleton runner) | PLANNER |
| `planner/contracts/specification.py` | `PlanningRecord`, `BuildSpecification`, action types (consumed cross-role) | PLANNER |
| `planner/contracts/task_todo.py` | `Build`/`TaskTodo`, `paths_overlap` (consumed by builder) | PLANNER |
| `planner/contracts/coverage.py` | Issue taxonomy ↔ structural concern mapping | PLANNER |
| `planner/contracts/validation.py` | Semantic validators for planning records (moved from shared validation; scanner detector retired) | PLANNER |

### 3.5 researcher — sourced evidence investigation

| File | Description | Role |
|---|---|---|
| `researcher/SKILL.md` | Role instructions: two read-only tools, honest result states, no web claims | RESEARCHER |
| `researcher/research.yaml` | 3-segment pipeline (review / retrieve / main), all unbound, read-only | RESEARCHER |
| `researcher/__init__.py` | Package marker | — |
| `researcher/__main__.py` | stdin-envelope CLI; constructs `ResearchContext` with `providers=None` | RESEARCHER |
| `researcher/researching.py` | Bounded model/tool loop (`search()`); `ProviderRegistryProtocol` injected by caller; no live provider implementation exists → fail-closed `ProviderError` | RESEARCHER |
| `researcher/research_catalog.py` | Loads the synthetic catalog, deterministic intent/keyword matching | RESEARCHER |
| `researcher/research_lifecycle.py` | Durable parent-child research case management over existing stores (CAS + receipts, crash-safe) | RESEARCHER |
| `researcher/contracts/research.py` | Research stage models (request/admission/output/review/fixtures) | RESEARCHER |
| `researcher/contracts/validation.py` | Semantic validators for research records (moved from shared validation) | RESEARCHER |

### 3.6 spec_search — unrouted retrieval capability

| File | Description | Role |
|---|---|---|
| `spec_search/SKILL.md` | Deterministic lexical retrieval docs; no stage, no dispatch route (`unrouted_capabilities` in breakdown.yaml) | SPEC_SEARCH |
| `spec_search/spec_search.yaml` | Mini-pipeline: normalize → collect → rank; read-only | SPEC_SEARCH |
| `spec_search/__init__.py` | Package marker | — |
| `spec_search/__main__.py` | Thin CLI adapter | SPEC_SEARCH |
| `spec_search/spec_search.py` | argparse CLI | SPEC_SEARCH |
| `spec_search/spec_searching.py` | Ranked snippet search with content digests, explicit budgets and skips | SPEC_SEARCH |

## 4. Shared contracts / storage / host — `agents/skills/shared/`

| File | Description | Role |
|---|---|---|
| `shared/__init__.py` | Package marker | — |
| `contracts/__init__.py` | Package marker | — |
| `contracts/workflow/__init__.py` | Re-exports primitives (now sourced from `agents.shared.base`) | SHARED |
| `contracts/workflow/system/config.py` | `AppConfig` pieces: `ProviderSelection`, `StateConfig`, `BudgetConfig` | HOST config |
| `contracts/workflow/system/coverage.py` | `PlanningCoverage` (9 lines) | PLANNER |
| `contracts/workflow/system/host.py` | Host-only evidence types: dispatch envelope/result, all receipts, `OperationRecord`, `admission_receipt_subject` (`Checkpoint` relocated to storage) | HOST / BUILDER |
| `contracts/workflow/system/observability.py` | `TraceContext` only (`EventStatus`/`ExecutionEvent` relocated to the event store) | HOST |
| `contracts/workflow/system/provider.py` | `ProviderProtocol`, `ProviderConfig` (validated YAML contract) | HOST config |
| `contracts/workflow/system/tool_registry.py` | `ToolId`/`StageId`, `ToolRegistrySnapshot`, `resolve_invocation`, `safe_relative_path` — consumed by BOTH builder and planner | SHARED (builder + planner) |
| `contracts/workflow/validation/structural.py` | Structural gap checks: source closure, effect gates, `CONCERNS`, `tool_invocation_gaps` | SHARED |
| `contracts/workflow/validation/cross_stage.py` | Cross-stage lineage/coverage/acyclicity (imports auditor + planner + researcher models) | SHARED |
| `contracts/workflow/validation/lineage.py` | Artifact chain validation | SHARED |
| `contracts/workflow/validation/protocols.py` | `ArtifactResolver`/`EvidenceResolver` protocols | SHARED |
| `storage/artifact_store.py` | Content-addressed artifact store with CAS revisions | HOST storage |
| `storage/canonical_serialization.py` | RFC 8785/JCS canonical bytes + SHA-256 digests (`SERIALIZER_PROFILE`) | HOST storage |
| `storage/checkpoint_store.py` | CAS checkpoint store; owns the `Checkpoint` model | HOST / BUILDER storage |
| `storage/event_store.py` | `EventStore` (sqlite) + hash-chained `AppendOnlyEventStore`; owns `EventStatus`/`ExecutionEvent` | HOST storage |
| `storage/receipt_store.py` | Host-only immutable receipt store (issue/verify, idempotent) | HOST storage |
| `storage/runtime_root_registry.py` | Trusted root registration; absolute non-symlink path safety | HOST |
| `tools/__init__.py` | Package marker | — |
| `tools/fs_walk.py` | Bounded root-safe traversal (shared skip list) | SHARED |
| `tools/sys_scan.py` | Passive interpreter capability probe (never installs monitoring hooks) | SHARED |
| `tools/verify_all.py` | Compares recorded scanner observations against accepted checks — ⚠ imports missing `planner.contracts.scanner`; no active callers | HOST verification (dormant) |
| `host/file_operations.py` | `write_atomic`/`move_file`/`remove_file` | BUILDER (only consumer) |
| `host/loaders.py` | YAML config loaders (`load_app_config`, `load_selected_provider`) | HOST (only consumer: `scripts/doctor.py`) |
| `host/recovery.py` | Recovery read/repair helpers | HOST (no active consumer found) |
| `host/recovery_readiness.py` | Recovery readiness model | HOST (no active consumer found) |
| `host/sys_path.py` | `resolve_allowed_path` | BUILDER |
| `host/sys_policy_enforcer.py` | `AuthorizationEngine` — allowed-roots policy enforcement | BUILDER |

## 5. Root `system/` package

| File | Description | Role |
|---|---|---|
| `system/__init__.py` | Package marker | — |
| `system/scanner/_types.py` | Engine-internal types (`EngineOutcome`, `FileEntry`, `SystemScanReport`, `Verdict`); timestamp-free for byte-identical output | HOST scanner |
| `system/scanner/_index.py` | Deterministic read-only repository index: sorted walk, per-file hashes, reports unreadable files | HOST scanner |
| `system/scanner/_predict.py` | Experimental baseline-manifest vs target-tree comparison; `indeterminate` over guessing | HOST scanner |
| `system/scanner/_preflight.py` | Retired-path + import-boundary detectors; ledger/rules supplied by the caller (decision D5) | HOST scanner |
| `system/scanner/_debug.py` | Syntax-error + duplicate-candidate detectors (static AST only) | HOST scanner |
| `system/scanner/__init__.py` | Public re-export surface of the scanner engine | HOST scanner |
| `system/scanner/__main__.py` | CLI: one JSON report to stdout, mode `debug|preflight|predict` | HOST scanner |
| `system/storage/_ref.py` | Canonical `kind:ident` reference strings (6 known kinds) | HOST storage |
| `system/storage/event.py` | Append-only event log entries for todos | HOST storage |
| `system/storage/queue.py` | File-backed durable queue store: todos, exec revisions, JSONL event logs, captured outputs; queue persists here, never in `agents/` (user ruling recorded in module docstring) | HOST storage |
| `system/storage/task_todo.py` | `TaskTodo` — requested work only, no status/scheduling | HOST storage |
| `system/storage/exec_todo.py` | `ExecTodo` + `ExecStatus` — one execution attempt against one exact todo revision | HOST storage |
| `system/memory/python/session.py` | **Empty file** — memory scaffold, unimplemented | HOST memory (placeholder) |
| `system/memory/typescript/session.ts` | **Empty file** — memory scaffold, unimplemented | HOST memory (placeholder) |
| `system/memory/tmp/blank.txt` | Empty placeholder | — |

## Consistency observations (evidence from reading the files)

1. **`agent.*` vs `agents.*` naming drift** — all six SKILL.md files and `auditor/references/audit_guidance.md` reference `agent.skills.*` / `system.host.skill_dispatch` (singular), while the actual package is `agents` (plural, per `pyproject.toml`: `packages = ["agents"]`).
2. **Missing scanner contract** — `planner/plan.yaml` line 8 declares `artifact_contract_refs: [agents/skills/planner/contracts/scanner.py]`; the file does not exist. The same module is imported by `shared/tools/verify_all.py` (the single pre-existing mypy error). Per `planner/contracts/validation.py`, the scanner stack was retired and replaced by `system/scanner` — both references are stale.
3. **Duplicated check order** — `audit_guidance.md` lines 15–16 repeat the same capability order twice (once with "verification", once without).
4. **Catalog path drift** — `agents/catalog/examples/modal_serverless_github_case.md` references `agent/catalog/research_samples.yaml` (singular).
5. **Migration state** — the storage-ownership pass (primitives to `agents/shared/base.py`, `Checkpoint`/`ExecutionEvent` to their storage owners, `common.py` deleted) is applied in the worktree but **verification was not completed** (ruff/mypy/pytest post-change runs pending). Baseline at `61790f0`: ruff clean, mypy 1 error (item 2 above), pytest 114 passed.




