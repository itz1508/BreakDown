"""Builder skill — execute admitted Build actions, report effects and evidence.

Ownership:
    Execute admitted Build actions, report effects and execution evidence.
    The Builder never issues trusted receipts, never authorizes its own
    operations, and never bypasses Build admission. All Build actions must
    be admitted by the Runtime host through a Package Lock and admission
    receipt before execution.

Tools:
    build_execution — execute admitted file operations (create, modify, move, remove)
    effect_verification — verify pre/post image digests and effect observations

Runtime integration:
    Results are reported through HostDispatchResult. The Runtime host
    validates admission, executes effects through EffectExecutor, and
    issues operation receipts.
"""

from agent.skills.builder.run import post_dispatch, pre_dispatch

__all__ = ["post_dispatch", "pre_dispatch"]
