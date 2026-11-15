"""Model-facing tools shared by every agent skill.

The reference structure follows anthropics/claude-quickstarts ``agents/tools``:
a plain Tool dataclass, per-tool modules, and server-tool declarations that the
provider executes. Adaptations for this repository: filesystem and search tools
are root-scoped and refuse escapes, and execution effects stay behind the
host's tool-registry authorization instead of a bare subprocess.
"""

from __future__ import annotations

from typing import Any

from agents.tools.base import Tool
from agents.tools.code_execution import CodeExecutionServerTool
from agents.tools.file_tools import FileReadTool, FileWriteTool, ReadSourceTool
from agents.tools.search import RepositorySearchTool
from agents.tools.think import ThinkTool
from agents.tools.web_search import WebSearchServerTool

__all__ = [
    "CodeExecutionServerTool",
    "FileReadTool",
    "FileWriteTool",
    "ReadSourceTool",
    "RepositorySearchTool",
    "ThinkTool",
    "Tool",
    "WebSearchServerTool",
    "manifest",
]

# Tools available per v3 workflow stage (agent/breakdown.yaml). Stages absent
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
    """Return per-stage tool declarations in provider format for the given root."""
    manifest: dict[str, list[dict[str, Any]]] = {}
    for stage, tool_types in _STAGE_TOOLS.items():
        manifest[stage] = [tool_type(root=root).to_openai_dict() for tool_type in tool_types]  # type: ignore[call-arg]
    return manifest
