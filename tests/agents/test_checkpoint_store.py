"""Regression coverage for the repaired CheckpointStore.

The load/record/update methods were displaced into the Checkpoint model
during the storage-ownership relocation (fixed in a8c188eef037c84a134956aa
58a7d644fce721d0). These tests exercise the actual sqlite-backed behavior
of ``agents.skills.shared.storage.checkpoint_store.CheckpointStore`` —
method presence alone does not protect that repair.
"""

from __future__ import annotations

from pathlib import Path

from agents.skills.shared.storage.checkpoint_store import (
    Checkpoint,
    CheckpointStore,
)


def test_checkpoint_cas_then_load_returns_persisted_state(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path)
    revision, digest = store.checkpoint_cas("task-1", 0, {"stage": "probe"})

    assert revision == 1
    loaded = store.load_checkpoint("task-1")
    assert loaded is not None
    loaded_revision, loaded_state, loaded_digest = loaded
    assert loaded_revision == revision
    assert loaded_state == {"stage": "probe"}
    assert loaded_digest == digest


def test_load_checkpoint_returns_none_for_unknown_task(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path)
    store.checkpoint_cas("task-1", 0, {"stage": "probe"})

    assert store.load_checkpoint("no-such-task") is None


def test_record_and_update_operation_ledger(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path)
    revision, _ = store.checkpoint_cas("task-1", 0, {"stage": "probe"})

    op_id = store.record_operation("task-1", revision, "create", "probe.py")
    assert op_id > 0

    store.update_operation_status(op_id, "completed")


def test_checkpoint_model_is_storage_owned_and_frozen() -> None:
    """The Checkpoint model lives in this module (storage identity) and is immutable."""
    checkpoint = Checkpoint(
        checkpoint_id="cp-1",
        checkpoint_revision=1,
        checkpoint_digest="a" * 64,
        task_id="task-1",
        run_id="run-1",
        stage="research",
        phase="probe",
        stage_revision=1,
    )
    assert checkpoint.checkpoint_id == "cp-1"
    try:
        checkpoint.checkpoint_id = "cp-2"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Checkpoint must be frozen (immutable)")

