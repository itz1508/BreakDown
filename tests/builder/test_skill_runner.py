"""Builder delegates approved actions rather than inventing authorization."""

from unittest.mock import Mock

import pytest

from agent.skills.builder import file_operations
from agent.skills.builder.build import run
from system.host.skill_dispatch import BuildArguments


def test_builder_delegates_admitted_effect() -> None:
    executor = Mock()
    context = Mock()
    context.build_executor.return_value = executor
    receipt = Mock()
    args = BuildArguments(action_id="action", action_kind="modify", admission_receipt=receipt,
                          target_path="src/hello.py", content="print('ok')\n")
    expected = object()
    executor.execute_admitted.return_value = expected
    assert run(context, Mock(), args) is expected
    executor.execute_admitted.assert_called_once_with(
        action_id="action", action_kind="modify", admission_receipt=receipt,
        target_path="src/hello.py", source_path=None, content="print('ok')\n",
        expected_source_digest=None, wave=None,
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
