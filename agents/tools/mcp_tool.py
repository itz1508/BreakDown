"""Tool wrapper for MCP server connections."""

from __future__ import annotations

from typing import Any, Protocol

from agents.tools.base import Tool


class MCPConnection(Protocol):
    """Minimal surface an MCP connection must expose."""

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


class MCPTool(Tool):
    """Expose one MCP server tool through the shared Tool interface.

    The connection is injected; this module never constructs one. Only text
    results are supported today.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        connection: MCPConnection,
    ) -> None:
        super().__init__(name=name, description=description, input_schema=input_schema)
        self.connection = connection

    async def execute(self, **kwargs: Any) -> str:
        """Call the MCP tool and return its first text result."""
        try:
            result = await self.connection.call_tool(self.name, arguments=kwargs)
        except Exception as exc:
            return f"Error executing {self.name}: {exc}"
        content = getattr(result, "content", None)
        for item in content or []:
            if getattr(item, "type", None) == "text":
                return item.text
        return "No text content in tool response"
