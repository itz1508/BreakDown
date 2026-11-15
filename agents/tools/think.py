"""Reasoning scratchpad: the one tool with no external effects."""

from __future__ import annotations

from agents.tools.base import Tool


class ThinkTool(Tool):
    """Record a thought and hand it back. Reads nothing, changes nothing."""

    def __init__(self, root: str | object | None = None) -> None:
        del root  # uniform constructor signature; the think tool is scope-free
        super().__init__(
            name="think",
            description=(
                "Reasoning scratchpad for complex multi-step work. Records a "
                "thought and returns it; it never reads files, contacts "
                "anything, or changes state. Use it between tool calls to "
                "plan a search, evaluate what was found, or decide the next "
                "step."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "The thought to record.",
                    }
                },
                "required": ["thought"],
            },
        )

    def execute(self, thought: str) -> str:  # type: ignore[override]
        """Return the recorded thought verbatim; nothing else happens."""
        return thought
