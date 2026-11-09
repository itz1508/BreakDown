"""Provider-neutral standalone Sandbox core; never imports OneShot host modules."""

from .contracts import SandboxExecutionRequest, SandboxExecutionResult

__all__ = ["SandboxExecutionRequest", "SandboxExecutionResult"]
