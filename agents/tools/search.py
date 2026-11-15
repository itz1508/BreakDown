"""Repository text search: literal terms over scoped files with bounded output."""

from __future__ import annotations

from pathlib import Path

from agents.tools.base import Tool, resolve_scoped

_SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".mypy_cache"}
_MAX_FILE_BYTES = 1_000_000


class RepositorySearchTool(Tool):
    """Search repository text for literal terms; returns path, line and snippet."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        super().__init__(
            name="search_repository",
            description="Search repository text for literal terms; returns path, line and snippet per match.",
            input_schema={
                "type": "object",
                "properties": {
                    "terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 4,
                        "description": "Literal terms to search for",
                    },
                    "scope": {"type": "string", "description": "Subdirectory to restrict the search to"},
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Maximum number of matches returned",
                    },
                },
                "required": ["terms"],
                "additionalProperties": False,
            },
        )

    def execute(  # type: ignore[override]
        self,
        terms: list[str],
        scope: str = ".",
        max_results: int = 10,
    ) -> str:
        max_results = max(1, min(max_results, 50))
        try:
            base = resolve_scoped(self.root, scope)
        except ValueError:
            return f"Error: {scope} escapes the authorized root"
        if not base.is_dir():
            return f"Error: {scope} is not a directory"
        matches: list[str] = []
        for file_path in sorted(base.rglob("*")):
            if len(matches) >= max_results:
                break
            if not file_path.is_file() or file_path.stat().st_size > _MAX_FILE_BYTES:
                continue
            if any(part in _SKIP_DIRS for part in file_path.parts):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if any(term in line for term in terms):
                    relative = file_path.relative_to(self.root).as_posix()
                    matches.append(f"{relative}:{line_number}: {line.strip()}")
                    if len(matches) >= max_results:
                        break
        if not matches:
            return f"No matches for {terms} under {scope}"
        return "\n".join(matches)
