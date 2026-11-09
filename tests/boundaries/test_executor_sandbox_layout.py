"""Regression: exactly one isolated Sandbox implementation under Executor."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "agent/skills/executor/sandbox_v3"


def test_sandbox_implementation_is_under_executor() -> None:
    required = (
        "pyproject.toml",
        "uv.lock",
        "src/modal_build_sandbox/contracts.py",
        "src/modal_build_sandbox/modal_runtime.py",
        "src/modal_build_sandbox/snapshot.py",
        "src/modal_build_sandbox/applicator.py",
        "src/modal_build_sandbox/policy.py",
        "src/modal_build_sandbox/evidence.py",
        "src/modal_build_sandbox/recovery.py",
        "src/modal_build_sandbox/runner.py",
        "tests/test_contracts.py",
        "tests/integration/test_modal_e2e.py",
    )
    assert all((SANDBOX / p).is_file() for p in required)
    assert not (ROOT / "deployment/modal/sandbox_v3").exists()


def test_executor_does_not_own_host_persistence_or_authorization() -> None:
    for module in ("artifact_store", "authorization", "checkpoint_store", "receipt_store", "event_store"):
        assert (ROOT / "agent/runtime" / f"{module}.py").is_file()
        assert not (ROOT / "agent/skills/executor" / f"{module}.py").exists()
