# Workflow output validation — TODO execution and connected-workflow gap

Baseline: `itz1508/breakdown`, `breakdown-staging`, `3ef57f5801cc2e88c8a692c08505b49ebb14f268`.

## Scope and evidence

One fixture-backed TODO E2E test validates **supplied BuildSpecification → compiled TaskTodo → admitted physical effects → durable restart → independently executed program**. This is not a connected Research/Audit/Planning/Fixture Validation/Build/Build Validation workflow run. The supplied Research and Audit inputs are deliberately synthetic; no stage-completion receipts or transition evidence is fabricated.

Existing focused contract, security, and recovery tests remain intact. The separate six-stage workflow E2E remains **blocked, not implemented**.

The test uses the existing `BuildSpecification`, `compile_build`, `WorkPlan`, `PackageLock`, `BuildAdmission`, `EffectExecutor`, and Host-owned stores. It compares the complete generated TODO list and execution waves with the independent `tests/fixtures/task_todo.json` oracle, tests a semantic mutation, rejects unauthorized/early execution, reloads durable state, and verifies actual subprocess stdout/stderr/exit status.

## Collection

Default pytest import mode collides on same-named test modules in different directories. `--import-mode=importlib` avoids that collision without renaming existing tests.

## Connected-workflow gap

The staging source still contains obsolete `mvp` import paths in the Researcher and CLI, and `system/host/workflow_control.py` refers to an absent legacy workflow configuration. **Do not restore or recreate MVP or invent an MVP shim.** Audit and rewire legacy call sites only through the established Researcher implementation and Host ownership; do not fabricate provider settings, source evidence, receipts, or success paths.

The default Research catalog references a path not present in the inspected branch; other provider/guidance assets also require source-of-truth reconciliation. Static structural checks are not evidence that connected execution succeeded.

Once authorized runtime wiring exists, add one `tests/e2e/test_workflow_e2e.py` and `tests/fixtures/workflow.json`. Use actual Host dispatch/return, validate each persisted model with existing contract validators and exact upstream lineage, compare typed output to independently defined fixture expectations, exercise the real fixture validator and Builder, and run independent Build Validation. Prove completion only after `complete_final_stage` and a durable-state reopen.

## Verification

Run:
- `uv run --no-sync pytest tests/e2e/test_task_todo_e2e.py`
- `uv run --no-sync pytest tests/e2e/test_work_todo.py tests/contracts/test_task_todo_compile.py tests/e2e/test_real_workflow.py tests/builder/test_skill_runner.py tests/planner/test_skill_runner.py tests/e2e/test_task_todo_e2e.py`
- `uv lock --check`
- `uv run --no-sync ruff check tests/e2e/test_task_todo_e2e.py`
- `uv run --no-sync ruff format --check tests/e2e/test_task_todo_e2e.py`

### Prior supplied verification (not independently rerun in this environment)

The submitted patch report: TODO scenario passes, focused selection **48 passed**; modified-test lint/format and lock pass. Branch-wide **453 passed, 33 failed, 53 errors**, versus pristine **452 passed, 33 failed, 53 errors**, with the same reported failures and errors. This environment lacks a checkout and cannot independently run the project suite.

No production source was altered by this test change. No connected provider execution or six-stage E2E is claimed.
