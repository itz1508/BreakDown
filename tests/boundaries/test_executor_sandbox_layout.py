"""Regression: exactly one isolated Sandbox implementation under Executor."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "agent/skills/executor/sandbox"


def test_sandbox_implementation_is_under_executor() -> None:
    required = (
        "pyproject.toml",
        "uv.lock",
        "src/oneshot_sandbox/contracts.py",
        "src/oneshot_sandbox/integrations/modal.py",
        "src/oneshot_sandbox/backend.py",
        "src/oneshot_sandbox/integrations/__init__.py",
        "src/oneshot_sandbox/snapshot.py",
        "src/oneshot_sandbox/applicator.py",
        "src/oneshot_sandbox/policy.py",
        "src/oneshot_sandbox/evidence.py",
        "src/oneshot_sandbox/recovery.py",
        "src/oneshot_sandbox/runner.py",
        "tests/test_contracts.py",
        "tests/integration/test_modal_e2e.py",
    )
    assert all((SANDBOX / p).is_file() for p in required)
    assert not (ROOT / "deployment/modal/sandbox_v3").exists()
    assert not (ROOT / "agent/skills/executor/sandbox_v3").exists()


def test_executor_does_not_own_host_persistence_or_authorization() -> None:
    for module in ("artifact_store", "authorization", "checkpoint_store", "receipt_store", "event_store"):
        assert (ROOT / "agent/runtime" / f"{module}.py").is_file()
        assert not (ROOT / "agent/skills/executor" / f"{module}.py").exists()


def test_core_backend_does_not_duplicate_modal_adapter() -> None:
    assert not (SANDBOX / "src/oneshot_sandbox/modal_runtime.py").exists()
    assert not (SANDBOX / "src/modal_build_sandbox").exists()
    assert (SANDBOX / "src/oneshot_sandbox/integrations/modal.py").is_file()
