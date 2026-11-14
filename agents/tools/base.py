"""Model-facing tool definitions shared by every agent skill.

Layering: this package defines the tools a model can call (name, description,
input schema, execute). Role-owned workflow operations live in
``agents/skills/<role>/tools`` and cross-role implementations in
``agents/skills/shared/tools``; this package wraps and exposes them to model
requests. Tools are authorization-aware: filesystem tools refuse to operate
outside their configured root.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Tool:
    """Base class for all model-facing agent tools."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return the Anthropic tool-use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def to_openai_dict(self) -> dict[str, Any]:
        """Return the OpenAI chat-completions function format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the provided parameters."""
        raise NotImplementedError("Tool subclasses must implement execute()")


def resolve_scoped(root: Path | None, path: str) -> Path:
    """Resolve ``path`` against ``root`` and refuse anything outside it.

    Relative paths are interpreted relative to the root, not the process
    working directory. ``Path.resolve`` follows symlinks, so a link planted
    inside the root that points outside is rejected as well. Without a root
    the path is returned resolved, for direct (non-agent) CLI use.
    """
    path_obj = Path(path)
    if root is None:
        return path_obj.resolve()
    root_path = Path(root).resolve()
    candidate = path_obj if path_obj.is_absolute() else root_path / path_obj
    resolved = candidate.resolve()
    resolved.relative_to(root_path)
    return resolved
