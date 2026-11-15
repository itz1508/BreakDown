"""Think tool for internal reasoning without external effects."""

from __future__ import annotations

from agents.tools.base import Tool


class ThinkTool(Tool):
    """Reasoning scratchpad: never obtains new information or mutates state."""

    def __init__(self, root: str | object | None = None) -> None:
        del root  # uniform constructor signature; the think tool is scope-free
        super().__init__(
            name="think",
            description=(
                "Use the tool to think about something. It will not obtain "
                "new information or change any state, but just append the "
                "thought to the log. Use it when complex reasoning or some "
                "cache memory is needed."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "A thought to think about.",
                    }
                },
                "required": ["thought"],
            },
        )

    def execute(self, thought: str) -> str:  # type: ignore[override]
        """Return the thought back to the model; nothing else happens."""
        return "Thinking complete!"
