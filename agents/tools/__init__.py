"""Model-facing tools shared by every role.

Owns the tool surface a model sees: root-scoped filesystem and search tools,
the reasoning scratchpad, and provider-executed server-tool declarations.
Role-owned workflow operations live in ``agents/skills/<role>/tools``; this
package never hardcodes a provider wire format.
"""

from __future__ import annotations

from typing import Any

from agents.tools.base import Tool, resolve_scoped
from agents.tools.file_tools import FileReadTool, FileWriteTool, ReadSourceTool
from agents.tools.search import RepositorySearchTool
from agents.tools.server import ServerTool
from agents.tools.think import ThinkTool

__all__ = [
    "FileReadTool",
    "FileWriteTool",
    "ReadSourceTool",
    "RepositorySearchTool",
    "ServerTool",
    "ThinkTool",
    "Tool",
    "manifest",
    "resolve_scoped",
]

# Tools available per v3 workflow stage (agents/breakdown.yaml). Stages absent
# here dispatch no model tools.
_STAGE_TOOLS: dict[str, tuple[type[Tool], ...]] = {
    "discovery": (RepositorySearchTool, ReadSourceTool, ThinkTool),
    "research": (RepositorySearchTool, ReadSourceTool, ThinkTool),
    "repository_reconciliation": (RepositorySearchTool, ReadSourceTool, ThinkTool),
    "gap_inspection": (RepositorySearchTool, ReadSourceTool, ThinkTool),
    "planning": (ReadSourceTool, ThinkTool),
    "sandbox_execution": (FileWriteTool, ThinkTool),
}


def manifest(root: str | Any) -> dict[str, list[dict[str, Any]]]:
    """Return per-stage tool declarations in neutral format for the given root."""
    manifest_map: dict[str, list[dict[str, Any]]] = {}
    for stage, tool_types in _STAGE_TOOLS.items():
        manifest_map[stage] = [tool_type(root=root).declaration() for tool_type in tool_types]  # type: ignore[call-arg]
    return manifest_map
