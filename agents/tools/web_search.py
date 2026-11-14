"""Anthropic server tools: executed provider-side, declared client-side only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WebSearchServerTool:
    """Web search server tool in Anthropic's server-tool format."""

    name: str = "web_search"
    type: str = "web_search_20250305"
    max_uses: int | None = None
    allowed_domains: list[str] | None = None
    blocked_domains: list[str] | None = None
    user_location: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the Anthropic server-tool declaration."""
        tool: dict[str, Any] = {"type": self.type, "name": self.name}
        if self.max_uses is not None:
            tool["max_uses"] = self.max_uses
        if self.allowed_domains is not None:
            tool["allowed_domains"] = self.allowed_domains
        if self.blocked_domains is not None:
            tool["blocked_domains"] = self.blocked_domains
        if self.user_location is not None:
            tool["user_location"] = self.user_location
        return tool


@dataclass
class CodeExecutionServerTool:
    """Code execution server tool in Anthropic's server-tool format."""

    name: str = "code_execution"
    type: str = "code_execution_20250522"

    def to_dict(self) -> dict[str, Any]:
        """Return the Anthropic server-tool declaration."""
        return {"type": self.type, "name": self.name}
