"""Builder delegates approved actions rather than inventing authorization."""

from unittest.mock import Mock

from agent.runtime.skill_dispatch import BuildArguments
from agent.skills.builder.run import run


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
