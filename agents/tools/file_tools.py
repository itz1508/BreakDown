"""Filesystem tools: bounded reads, listing, writes and edits under a root."""

from __future__ import annotations

from pathlib import Path

from agents.tools.base import Tool, resolve_scoped

_MAX_LIST_ENTRIES = 500


class FileReadTool(Tool):
    """Read file contents or list directory entries inside the scoped root."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root).resolve() if root is not None else None
        super().__init__(
            name="file_read",
            description=(
                "Read files or list directory contents.\n\n"
                "Operations:\n"
                "- read: Read the contents of a file (bounded by max_lines)\n"
                "- list: List files in a directory (bounded entry count)"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "list"],
                        "description": "File operation to perform",
                    },
                    "path": {"type": "string", "description": "File path for read or directory path for list"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum lines to read (0 means no limit)",
                    },
                    "pattern": {"type": "string", "description": "Glob pattern for the list operation"},
                },
                "required": ["operation", "path"],
            },
        )

    def execute(  # type: ignore[override]
        self, operation: str, path: str, max_lines: int = 0, pattern: str = "*"
    ) -> str:
        if operation == "read":
            return self._read_file(path, max_lines)
        if operation == "list":
            return self._list_files(path, pattern)
        return f"Error: Unsupported operation '{operation}'"

    def _read_file(self, path: str, max_lines: int = 0) -> str:
        try:
            file_path = resolve_scoped(self.root, path)
            if not file_path.exists():
                return f"Error: File not found at {path}"
            if not file_path.is_file():
                return f"Error: {path} is not a file"
            with open(file_path, encoding="utf-8", errors="replace") as handle:
                if max_lines > 0:
                    lines = []
                    for index, line in enumerate(handle):
                        if index >= max_lines:
                            break
                        lines.append(line)
                    return "".join(lines)
                return handle.read()
        except ValueError:
            return f"Error: {path} escapes the authorized root"
        except OSError as exc:
            return f"Error reading {path}: {exc}"

    def _list_files(self, directory: str, pattern: str = "*") -> str:
        try:
            dir_path = resolve_scoped(self.root, directory)
            if not dir_path.exists():
                return f"Error: Directory not found at {directory}"
            if not dir_path.is_dir():
                return f"Error: {directory} is not a directory"
            entries = sorted(
                str(entry.relative_to(dir_path)) if dir_path != entry else entry.name
                for entry in dir_path.glob(pattern)
            )
            if not entries:
                return f"No entries matching {pattern} in {directory}"
            trimmed = entries[:_MAX_LIST_ENTRIES]
            suffix = "" if len(entries) <= _MAX_LIST_ENTRIES else f"\n... ({len(entries) - _MAX_LIST_ENTRIES} more)"
            return "\n".join(trimmed) + suffix
        except ValueError:
            return f"Error: {directory} escapes the authorized root"
        except OSError as exc:
            return f"Error listing {directory}: {exc}"


class FileWriteTool(Tool):
    """Write or edit a file inside the scoped root."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root).resolve() if root is not None else None
        super().__init__(
            name="file_write",
            description=(
                "Write files or make targeted edits.\n\n"
                "Operations:\n"
                "- write: Create or overwrite a file with content\n"
                "- edit: Replace old_text with new_text in an existing file"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["write", "edit"],
                        "description": "File operation to perform",
                    },
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write (write operation)"},
                    "old_text": {"type": "string", "description": "Text to replace (edit operation)"},
                    "new_text": {"type": "string", "description": "Replacement text (edit operation)"},
                },
                "required": ["operation", "path"],
            },
        )

    def execute(  # type: ignore[override]
        self,
        operation: str,
        path: str,
        content: str = "",
        old_text: str = "",
        new_text: str = "",
    ) -> str:
        if operation == "write":
            if not content:
                return "Error: content parameter is required"
            return self._write_file(path, content)
        if operation == "edit":
            if not old_text or not new_text:
                return "Error: both old_text and new_text parameters are required for edit operation"
            return self._edit_file(path, old_text, new_text)
        return f"Error: Unsupported operation '{operation}'"

    def _write_file(self, path: str, content: str) -> str:
        try:
            file_path = resolve_scoped(self.root, path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(content)
            return f"Successfully wrote {len(content)} characters to {path}"
        except ValueError:
            return f"Error: {path} escapes the authorized root"
        except OSError as exc:
            return f"Error writing to {path}: {exc}"

    def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        try:
            file_path = resolve_scoped(self.root, path)
            if not file_path.exists():
                return f"Error: File not found at {path}"
            if not file_path.is_file():
                return f"Error: {path} is not a file"
            content = file_path.read_text(encoding="utf-8", errors="strict")
            if old_text not in content:
                return f"Error: The specified text was not found in {path}"
            count = content.count(old_text)
            file_path.write_text(content.replace(old_text, new_text), encoding="utf-8")
            if count > 1:
                return f"Warning: Found {count} occurrences. All were replaced in {path}"
            return f"Successfully edited {path}"
        except ValueError:
            return f"Error: {path} escapes the authorized root"
        except UnicodeDecodeError:
            return f"Error: {path} appears to be a binary file"
        except OSError as exc:
            return f"Error editing {path}: {exc}"


class ReadSourceTool(Tool):
    """Read a bounded line window from one file inside the scoped root."""

    def __init__(self, root: str | Path | None = None, max_read_lines: int = 60) -> None:
        self.root = Path(root).resolve() if root is not None else None
        super().__init__(
            name="read_source",
            description="Read a bounded line window from one file inside the workspace.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "minimum": 1},
                    "max_lines": {"type": "integer", "minimum": 1, "maximum": max_read_lines},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        )

    def execute(self, path: str, start_line: int = 1, max_lines: int = 20) -> str:  # type: ignore[override]
        try:
            file_path = resolve_scoped(self.root, path)
            if not file_path.is_file():
                return f"Error: {path} is not a file"
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            window = lines[start_line - 1 : start_line - 1 + max_lines]
            if not window:
                return "Error: start_line beyond end of file"
            return "\n".join(window)
        except ValueError:
            return f"Error: {path} escapes the authorized root"
        except OSError as exc:
            return f"Error reading {path}: {exc}"
