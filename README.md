# Breakdown — Skill-based OneShot Runtime

Migration source: [OneShot-Continuing](https://github.com/itz1508/OneShot-Continuing) at `dbecd79e58b5b43592009d3cc914fcdc2722413b`. Destination baseline: `d53c0e8ace51bd811bc7af39e78a280a52391a21`.

## Executable role packages

| Skill | Entrypoint | Function |
| --- | --- | --- |
| Auditor | `agent.skills.auditor.audit` and `agent.skills.auditor.code_design` | Read-only source inspection and pre-Planning CodeDesign preparation |
| Researcher | `agent.skills.researcher.research` | Host-provisioned Research execution; blocks when no executor is configured |
| Planner | `agent.skills.planner.plan` | Host-driven Scanner, gap analysis, design review |
| Builder | `agent.skills.builder.build` | Only admitted effects through the Runtime executor |

`system.host.skill_dispatch` checks the persisted Host dispatch envelope before importing a role. Existing role ID `audit_discovery` is intentionally retained even though the package is named `auditor`.

## Trust and execution

Runtime retains controller, authorization, artifacts, receipts, event logs, Scanner gateway and evidence, specification freeze, package lock, build admission, effect execution and recovery. Skills do not mint trusted receipts or change stage transitions.

The source files in `agent/audit` are migrated to `agent/skills/auditor/checks`, `agent/gap_analysis.py` to `agent/skills/planner/checks/gap_analysis.py`, and `agent/research_catalog.py` to `system/host/research_catalog.py`.

**CodeDesign:** Audit Discovery owns source-grounded candidate preparation and evidence questions; Planning owns subsequent design decisions and `CodeDesignReview`. This is the preferred Python-facing terminology; the legacy `CodeIntent` wire field and persisted artifacts remain readable for compatibility until an independently validated storage and Vector Search migration occurs. No Databricks index was modified by this repository change.

## Local verification

```sh
uv sync --locked --extra meta
uv run --no-sync python -m agent skills
uv run --no-sync python -m agent doctor
uv lock --check
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy agent contracts system
uv run --no-sync pytest -q
```

The CLI and Scanner execution do not by themselves establish full connected workflow E2E completion. Independent Build Validation and recovery verification require executed evidence.

## Consolidation package status

The `consolidation/baseline-20261110` branch is an **unpromoted candidate**, not the active production baseline. The CI `package-integrity` job builds a wheel and a pinned source ZIP containing `uv.lock`, verifies the bundled Catalog and Meta provider configuration, enforces retired-path exclusions, and runs focused tests on Python 3.11 and 3.12. Published artifacts are available from that branch's GitHub Actions CI runs.

Retired `mvp/`, `.agents/`, and `oneshot_sandbox/` paths are not packaged or reconstructed. The production Researcher fails closed until a Host-provisioned executor is configured. Legacy MVP-specific tests, the full repository CI suite, exact frozen-action binding, and independent connected E2E verification remain **release blockers**; consult the individual CI jobs rather than treating wheel availability as certification.

