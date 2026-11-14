"""Anthropic server tool for provider-side code execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CodeExecutionServerTool:
    """Code execution server tool that uses Anthropic's server tool format."""

    name: str = "code_execution"
    type: str = "code_execution_20250522"

    def to_dict(self) -> dict[str, Any]:
        """Return the Anthropic server-tool declaration."""
        return {"type": self.type, "name": self.name}
