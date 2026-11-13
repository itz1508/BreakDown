"""Builder delegates approved actions rather than inventing authorization."""

from unittest.mock import Mock

import pytest

from agent.host import file_operations
from agent.host.skill_dispatch import BuildArguments
from agent.skills.builder.building import run


def test_builder_delegates_admitted_effect() -> None:
    executor = Mock()
    context = Mock()
    context.build_executor.return_value = executor
    receipt = Mock()
    args = BuildArguments(
        action_id="action",
        action_kind="modify",
        admission_receipt=receipt,
        target_path="src/hello.py",
        content="print('ok')\n",
    )
    expected = object()
    executor.execute_admitted.return_value = expected
    assert run(context, Mock(), args) is expected
    executor.execute_admitted.assert_called_once_with(
        action_id="action",
        action_kind="modify",
        admission_receipt=receipt,
        target_path="src/hello.py",
        source_path=None,
        content="print('ok')\n",
        expected_source_digest=None,
        wave=None,
    )
    context.host.receipt_store.issue_verified.assert_not_called()


def test_builder_file_operations_create_modify_move_remove(tmp_path) -> None:
    """Physical mutations remain independent of admission and receipt authority."""
    source = tmp_path / "main.py"
    target = tmp_path / "moved.py"

    file_operations.write_atomic(source, "original\n")
    assert source.read_text(encoding="utf-8") == "original\n"

    file_operations.write_atomic(source, "updated\n")
    assert source.read_text(encoding="utf-8") == "updated\n"

    file_operations.move_file(source, target)
    assert not source.exists()
    assert target.read_text(encoding="utf-8") == "updated\n"

    file_operations.remove_file(target)
    assert not target.exists()


def test_builder_atomic_write_cleans_temporary_file_on_failure(tmp_path, monkeypatch) -> None:
    target = tmp_path / "keep.py"
    target.write_text("original", encoding="utf-8")

    def interrupted(_source, _destination):
        raise OSError("simulated failed replacement")

    monkeypatch.setattr(file_operations.os, "replace", interrupted)
    with pytest.raises(OSError, match="simulated failed replacement"):
        file_operations.write_atomic(target, "new content")

    assert target.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.glob(".oneshot-tmp-*")) == []


def test_failed_pre_effect_checkpoint_cannot_create_parent_directory(tmp_path, monkeypatch) -> None:
    """A failed durable checkpoint must not cause even a parent mkdir."""
    from agent.host.contracts.system.host import BuildAdmissionReceipt, ReceiptRef
    from agent.skills.builder.contracts.build import BuildActionStatus
    from agent.skills.builder.effect_executor import EffectExecutor

    receipts = Mock()
    receipts.verify.return_value = True
    checkpoints = Mock()
    checkpoints.load_checkpoint.return_value = None
    authorization = Mock()
    workspace = tmp_path / "workspace"
    executor = EffectExecutor(authorization, checkpoints, receipts, workspace)
    lock_ref = ReceiptRef(receipt_id="lock", receipt_digest="0" * 64, issuer_id="host")
    admission_ref = ReceiptRef(receipt_id="admission", receipt_digest="1" * 64, issuer_id="host")
    admitted = BuildAdmissionReceipt(
        admission_id="test",
        lock_receipt_ref=lock_ref,
        authorized_action_ids=("action-1",),
        receipt_ref=admission_ref,
    )
    monkeypatch.setattr(
        executor,
        "_pre_effect_checkpoint",
        Mock(side_effect=OSError("checkpoint unavailable")),
    )
    result = executor.execute_admitted(
        action_id="action-1",
        action_kind="create",
        admission_receipt=admitted,
        target_path="uncreated/subdir/data.txt",
        content="data",
    )
    assert result.status is BuildActionStatus.FAILED
    assert not (workspace / "uncreated").exists()
