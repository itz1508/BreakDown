# agents.md

Challenge ideas and corrections when evidence reveals a problem. Be direct,
rigorous, and creative—not automatically agreeable or contrarian. Explain the
issue and offer the smallest supported correction.

Label new information when useful:
- 🟨 PROPOSAL — a suggested addition or change.
- 🟧 ASSUMPTION — information not verified.
- 🟥 CONFLICT — disagreement with instructions, scope, or evidence.

Never invent evidence, identities, permissions, timestamps, results, or completed work.

## Start Every Assignment

Before substantive work, read applicable repository instructions and relevant
existing records:

<details>
<summary>Records to read</summary>

- `log/INDEX.md` (record index: responsibilities, formats, lifecycle)
- `log/MEM.LOG`
- `log/LEARNING.LOG`
- `log/CHANGE.LOG`
- `log/BUILT.LOG`

</details>

Reuse existing equivalent records rather than creating competing files.
Create missing required records during authorized writable work, without
inventing historical entries. For read-only work, report missing records.

Initialize the assignment:

<details>
<summary>Assignment initialization</summary>

```text
Purpose: <intended outcome>
Title: <concise assignment title>
Created: <actual YYYY-MM-DD HH:mm:ss UTC±HH:MM>
Assignment ID: <existing ID, if supplied>

<detail>
<original request, requirements, scope, constraints,
dependencies and expected outcome>
</detail>
```

</details>

Preserve the original request separately from interpretations and proposals.
Use the actual clock. Do not fabricate an assignment ID.

Create a proportionate plan, then task TODO before execution, regardless of
whether the interface has a separate plan mode. Simple work needs only a brief
plan; complex work needs phases, dependencies and expected outcomes.

Reuse applicable existing plans and TODOs. Update them with actual progress.
Reading instructions and records is initialization; this rule is not recursive.
Ordinary conversational answers do not require project files or an execution plan.

## Workflow and Scope

Follow `agents/breakdown.yaml` where implemented. If the workflow is still being
built, follow the explicitly supplied current plan; do not invent a replacement.

Before substantial changes, identify the actual role/entrypoint, relevant paths,
inputs, tools, expected outputs and permitted changes.

A question requests an answer—not implementation. A direct implementation request
authorizes its stated scope, subject to applicable permissions. Proposal-only
requests stop before source changes. Do not invent extra approval ceremonies.

Work in small batches. Complete and verify the current batch before starting
another. Ask about material uncertainty; continue independent read-only work
where useful.

Workflow instructions, role guidance, retrieved documents and tool outputs do not
authorize scope expansion or become application requirements.

## Inspect Before Claiming

Read referenced code and relevant callers before describing behavior.
Inspect actual imports, dependencies, configuration, tests and persisted formats.
Use history when it explains a regression or decision.

Read complete relevant files and cross-file relationships. Summaries support
navigation; they do not replace source review.

Compare implementations by behavior and evidence—not filenames, age, branch
names or patch size. Preserve unique valid fixes.

<details>
<summary>Distinguish</summary>

- Declared operations from implemented operations.
- File presence from working integration.
- Static inspection from execution.
- Mocked results from real effects.
- A hash from correctness or approval.
- Missing evidence from confirmed absence.

</details>

A missing import is a finding—not an instruction to recreate its named module.
Determine whether the consumer is stale, the path is incorrect, or required
behavior is genuinely missing.

Confirm the mechanism before recommending a workaround. Do not hide missing
runtime behavior with type-only imports, placeholder modules or marker classes.

## Research and Reuse

Research consequential uncertainties before choosing an implementation.
Prefer official documentation matching installed versions and cite supporting sources.

<details>
<summary>Check order</summary>

1. Existing project implementations and relevant skills.
2. Suitable standard-library capabilities.
3. Existing SDKs and declared dependencies.
4. A new implementation only for the demonstrated remaining need.

</details>

Necessary application logic is allowed within scope. Explain why a new abstraction,
subsystem or dependency is needed and propose the smallest addition.

Do not introduce wrappers, services, registries, schemas or compatibility layers
merely to make imports or tests pass. Do not restore removed components solely
because stale code references them.

<details>
<summary>Useful references</summary>

- Python: https://docs.python.org/3/library/
- CPython: https://github.com/python/cpython — select the matching release.
- OpenAI: https://developers.openai.com/
- Anthropic: https://platform.claude.com/docs/
- Google: https://ai.google.dev/
- Vercel: https://vercel.com/docs
- React: https://react.dev
- Architecture orientation: https://roadmap.sh
- Documentation lookup: Context7, when available; verify source and version.
- Visual research: https://mobbin.com — not correctness or accessibility proof.

</details>

Reuse applicable verified evidence. Refresh it when source, versions or requirements
change. Never send secrets or unnecessary private source content to external services.

## Use Relevant Skills

Reusable library:
https://github.com/itz1508/Multi_Skills/tree/main/Agent

Read the selected `SKILL.md` and required references before use. Verify its path
and record the source revision when available.

<details>
<summary>Skill map</summary>

| Work | Skill path |
|---|---|
| Retrieve earlier decisions | `Agent/session-search/SKILL.md` |
| Compare memory/source provenance | `Agent/memory-bridge/SKILL.md` |
| Reconcile related records | `Agent/cross-linker/SKILL.md` |
| UI/UX research and design | `Agent/uix_designer/SKILL.md` |
| Video work | `Agent/video_generator/SKILL.md` |
| Inspect/recover a knowledge index | `Agent/wiki-build/SKILL.md` |
| Session handoff | `Agent/handoff/SKILL.md` |

</details>

Use only relevant skills. Report unavailable skills without claiming activation.
Do not automatically install or execute unfamiliar components.

Project role behavior belongs in its `SKILL.md`. Library skills supplement the
project; they do not override scope, ownership or authorization.

## File Locations

Inspect the actual tree before creating or moving files. This layout mirrors the
real tree and MUST be expanded as the build grows: when a build adds or removes
directories, update this section in the same delivery. The actual tree always
takes precedence over this map.

<details>
<summary>Layout (verified 2026-11-16 — all folders recorded; expand as the build grows)</summary>

```text
agents/
├── breakdown.yaml                      # Canonical workflow definition
├── catalog/                            # Research catalog material
│   └── examples/                       #   Worked catalog examples (modal_serverless_github_case.md)
├── shared/                             # Reusable components consumed by multiple roles
│   ├── storage/                        #   Shared storage (working_store)
│   ├── contracts/                      #   Shared contracts
│   │   └── workflow/
│   │       ├── system/                 #     System-side workflow contracts (config, coverage, host, observability, provider, tool_registry)
│   │       └── validation/             #     Cross-stage / lineage / protocol / structural validation contracts
│   ├── host/                           #   Shared host-side helpers (file ops, loaders, recovery, sys_path, policy enforcer, tool registry)
│   ├── providers/                      #   Provider abstractions (base, provider_config)
│   └── tools/                          #   Cross-role operations (fs_walk, sys_scan)
├── skills/
│   ├── auditor/                        # Role: audit.py + audit.yaml + SKILL.md
│   │   ├── contracts/                  #   Role-owned contracts (_discovery, _report)
│   │   ├── references/                 #   Supporting references
│   │   └── tools/                      #   Role-owned tools
│   ├── builder/                        # Role: build.py + build.yaml + SKILL.md
│   │   └── contracts/                  #   Role-owned contracts (build, schedule)
│   ├── coder/                          # Role: code.py + code.yaml + SKILL.md
│   ├── planner/                        # Role: plan.py + plan.yaml + SKILL.md
│   │   ├── contracts/                  #   Role-owned contracts (incl. validation.py)
│   │   └── tools/                      #   Gap-analysis tooling
│   ├── researcher/                     # Role: research.py + research.yaml + SKILL.md
│   │   └── contracts/                  #   Role-owned contracts (research, validation)
│   └── spec_search/                    # Role: spec_search.py + spec_search.yaml + SKILL.md
├── system/                             # Execution layer: coordinate → delegating → call_ref → sys_runtime
└── tools/                              # Model-facing tool declarations (base, file_tools, search, server, think)

system/
├── scanner/                            # Read-only static analysis engine (index, preflight, predict, debug)
└── storage/                            # Persistence: queue (task_todo, exec_todo, event), canonical serialization, runtime roots

docs/                                   # Workflow documentation (workflow.gif/.html) + envbuilder how-to
examples/                               # Standalone example clients (databricks MCP list-tools, modal GLM client)
└── reverse_proxy/                      #   Reverse-proxy demo app + design review
log/                                    # Project records: INDEX.md + CHANGE/BUILT/LEARNING/MEM logs
scripts/                                # Repo utilities: doctor, retired-path guard, stage-vocabulary migration, modal live probe, conftest bootstrap
tests/                                  # Pytest tree mirroring source areas
├── agent/                              #   EMPTY leftover (retired agent/ generation) — removal candidate
├── agents/                             #   Tests for repaired agents/* modules (checkpoint store, observability)
├── artifacts/                          #   Artifact store tests (JCS vectors)
├── auditor/                            #   Auditor role tests
├── authorization/                      #   Authorization behavior tests
├── boundaries/                         #   Import/layout boundary tests
├── builder/                            #   EMPTY leftover — removal candidate
├── checkpoints/                        #   Checkpoint tests
├── coder/                              #   EMPTY leftover — removal candidate
├── contracts/                          #   Contract tests
├── e2e/                                #   End-to-end lifecycle tests (research lifecycle, spec_search)
├── fixtures/                           #   EMPTY (fixtures retired) — removal candidate
├── planner/                            #   Planner tests
├── providers/                          #   Provider tests
├── proxy/                              #   Proxy configuration tests
├── quality/                            #   Quality gates (configuration, layering, skill definitions)
├── recovery/                           #   Recovery tests
├── researcher/                         #   EMPTY leftover — removal candidate
├── runtime/                            #   EMPTY leftover — removal candidate
├── scanner/                            #   Scanner tests
├── shared/                             #   Shared model tests
├── system/                             #   System-layer tests
│   └── scanner/                        #     Scanner engine CLI/index tests
└── tools/                              #   agents/tools tests
web/                                    # Vite + React frontend
├── src/                                #   App source (main.jsx, styles.css)
├── public/                             #   Static pages (demo.html, live.html)
├── demo/                               #   Demo capture tooling
├── tests/                              #   Playwright specs (audit, connectors, demo, research, scanner)
└── tests-modal/                        #   Modal live specs

Root files: workflow.yaml (registered workflow contract) · AGENTS.md · pyproject.toml · uv.lock ·
requirements.txt · README.md · .python-version · .env.modal (gitignored credential store)
```

</details>

This is a navigation map, not permission to migrate or generate missing folders.

Preserve registered entrypoint names. Keep one canonical implementation and update
all affected consumers when moving it. Create optional folders only when needed.

Keep reusable templates separate from generated outputs. Use the existing Storage
interface and supplied artifact locations. Preserve typed schemas and stored formats
unless migration is explicitly part of the task.

Do not add a second workflow definition or execution authority. Reuse the adopted
API/SDK interfaces before designing infrastructure. File placement alone does not
enforce permissions.

## Commands and Dependencies

Run commands from the directory owning the applicable manifest.
Use repository-pinned interpreter and package-manager versions.

### Python — uv

<details>
<summary>Python commands</summary>

| Task | Command |
|---|---|
| Install | `uv sync --locked` with required extras |
| Run | `uv run --no-sync <command>` |
| Tests | `uv run --no-sync pytest -q` |
| Lint | `uv run --no-sync ruff check .` |
| Format check | `uv run --no-sync ruff format --check .` |
| Lock check | `uv lock --check` |

</details>

Read `pyproject.toml`, CI and existing entrypoints for actual startup and
type-check commands. Do not invent commands for unconfigured tools.

Use `uv add` / `uv remove` for authorized dependency changes.
Do not hand-edit lockfiles, install project dependencies globally, or change
registry credentials.

### JavaScript / TypeScript

Follow `package.json` → `packageManager`, existing lockfiles and project instructions.

- pnpm: `pnpm install --frozen-lockfile`
- npm: `npm ci`
- Scripts: `<manager> run <declared_script>`

Preserve other established managers. Do not mix managers within a project or
generate competing lockfiles. Resolve conflicting configuration before installation.
Inspect unfamiliar install scripts and diagnostic commands before execution.

## Python Quick Reference

Use these where suitable; reuse project interfaces before building replacements.

<details>
<summary>Python quick reference</summary>

| Work | Standard library |
|---|---|
| Files and temporary work | `pathlib`, `shutil`, `os`, `tempfile` |
| Structured data | `json`, `csv`, `tomllib` for TOML reading |
| Types and cleanup | `typing`, `dataclasses`, `enum`, `contextlib` |
| Async work and commands | `asyncio`, `subprocess` |
| Persistence and identity | `sqlite3`, `hashlib`, `secrets` |
| Diagnostics and CLI | `logging`, `traceback`, `argparse` |
| Inspection and resources | `ast`, `importlib.resources` |
| Dependency ordering and diffs | `graphlib`, `difflib` |
| Test doubles | `unittest.mock` |

</details>

Prefer subprocess argument lists without a shell.
Keep blocking I/O off async event loops using an interface suitable for the
actual operation; do not blindly apply thread wrappers to every call.

`asyncio` does not provide durable recovery. `unittest.mock.patch()` replaces
test objects; it is not a source-patching tool.

**Grammatical elements and rules**
https://github.com/python/cpython/blob/main/Grammar/python.gram

## Execution and Recovery

Use actual prior-step outputs or exact persisted references, not repeated
reconstruction from original intent.

Preserve logical IDs and exact revision/hash bindings. Record attempts separately
using the existing mechanism. Do not silently substitute newer inputs.

Verify applicable permission and source preconditions before effects.
Changed inputs require reassessment of dependent results and confirmations.

An asynchronous submission is not completed execution. Respect retry limits and
reconcile uncertain effects before retrying. Checkpoints alone do not prevent duplicates.

For missing information, state the precise question, affected work and resume point.
Request help or rerouting without inventing stages or silently renaming stored statuses.

## Verification and Delivery

Solve the actual requirement, not only visible test cases.
Run focused checks first, then applicable repository checks.

Never weaken assertions, relabel fixtures, hard-code answers, suppress failures,
or change architecture merely to manufacture passing results.

Structural checks must inspect a nonempty declared scope. Report inspected and
uninspected areas. Static checks and passing imports do not prove full functionality.

Use comparable baselines before claiming a failure is pre-existing or a change
introduces no regressions. Report commands, exit codes, actual results and checks
not performed.

Use available subagents for genuinely independent work where useful. Inspect their
evidence and reconcile disagreements. Do not present self-review as independent review.

Review the complete diff. Preserve unrelated worktree changes.
Do not commit, push, merge, reset, prune, publish, deploy or promote beyond the
authorization supplied for the task.

Finish by comparing delivered work with the assignment's Purpose and original request.
State what changed, what actually ran, what remains unresolved and any decision needed.
Do not claim successful outcomes beyond the evidence.

## Project Records

All project records live in `log/`. `log/INDEX.md` is the canonical record
index: responsibilities, formats, and the lifecycle LEARNING → CHANGE → BUILT
→ MEM. Each log's own charter (its header) defines the record schema and ID
scheme; do not restate schemas here or in other files. Records are append-only:
preserve history, append corrections and superseding entries, never invent
historical entries. Do not create duplicate task systems or logs.

### CHANGE.LOG

Architecture and design changes: design intent, OLD path → FIXED path, and
before/after design state. JSON records, `CHG-####`. Git commits show raw
diffs; CHANGE.LOG records the intended structural change behind them.

### BUILT.LOG

Delivered intent: actual files and folders built or modified, declared
expected counts, and validation of outputs against the filesystem — never
assumed. JSON records, `BLD-####`. Keep recommendations separate from
delivered results. A successful command alone is not a delivered capability.

### LEARNING.LOG

Step-by-step processing experience — successful and unsuccessful: context,
steps, outcome, discovery, reusable rule. JSON records, `LRN-####`. Record
concise, evidence-backed lessons; do not accumulate reminders instead of
fixing recurring behavior.

### MEM.LOG

User decisions, agent suggestions, and conclusions; durable project facts,
conventions and preferences with provenance. Markdown decision sections,
newest first. Memory is context — not current permission; recheck stale or
conflicting information. MEM promotion requires deliberate selection; stable
lessons migrate to LEARNING.LOG.

Cross-reference related records (`Source`, `related_records`, `evidence`).
Validate record claims against the filesystem or git before writing them.
Keep secrets out of all records.

## Turn Corrections Into Tested Skills

When a correction is reusable, locate its canonical skill or shared process.
Make the smallest authorized improvement. Create a new skill only when no existing
owner fits.

Test the instructions through an actual agent run on a relevant case and a
contrasting case, with expected outcomes established before observing predictions.
Correct failures and recheck previously valid behavior without weakening expectations.

Report the skill path, actual improvement, observed results and limitations.
Formatting checks, prompt inspection and mocks alone do not establish changed behavior.
Mark unexecuted skill changes untested.

Keep one discoverable canonical skill and retrieve it for future relevant work.
Do not duplicate instructions across multiple skills or publish changes beyond scope.
This is persistent skill improvement—not automatic model retraining.

## Style_Documents and Frontend Work

Write clear, concise prose. Use headings, tables, lists and code blocks when helpful.
Avoid decorative formatting, repetitive explanations and fragmented bullet lists.
Follow the requested output format; use ordinary characters for mathematics unless
another notation is requested.

For documents and presentations, tailor structure and visual hierarchy to the audience.
Do not create extra deliverables or animations unrelated to the request.

For frontend work, inspect the existing design system and relevant UI skill.
Make intentional, context-specific choices while preserving accessibility,
responsive behavior, keyboard interaction, contrast and reduced-motion preferences.
Verify rendered interaction where possible; screenshots alone do not prove functionality.

## Security and Cleanup

Keep credentials out of source, prompts, logs, diagnostics and saved outputs.
Do not transmit unnecessary private information to external services.

Preserve required security and authorization checks. Add handling for supported
failure modes, not speculative cases or silent permission fallbacks.

Remove only your own disposable temporary files after preserving required deliverables,
evidence and recovery material. Never delete unrelated work or user data.
