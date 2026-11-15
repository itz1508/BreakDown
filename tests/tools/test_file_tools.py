"""Filesystem tool tests: bounds, listing, writes, edits and root scoping."""

from __future__ import annotations

from agents.tools.file_tools import FileReadTool, FileWriteTool, ReadSourceTool


def test_read_returns_contents_and_respects_max_lines(tmp_path) -> None:
    (tmp_path / "note.txt").write_text("l1\nl2\nl3\n", encoding="utf-8")
    tool = FileReadTool(root=tmp_path)
    assert "l1" in tool.execute(operation="read", path="note.txt")
    assert tool.execute(operation="read", path="note.txt", max_lines=2) == "l1\nl2\n"


def test_read_refuses_paths_outside_root(tmp_path) -> None:
    (tmp_path / "secret.txt").write_text("outside", encoding="utf-8")
    tool = FileReadTool(root=tmp_path / "workspace")
    (tmp_path / "workspace").mkdir()
    assert "escapes the authorized root" in tool.execute(operation="read", path="../secret.txt")


def test_read_refuses_symlink_escape(tmp_path) -> None:
    import os

    if os.name == "nt":
        return  # symlink creation needs privileges on Windows
    (tmp_path / "workspace").mkdir()
    (tmp_path / "outside.txt").write_text("secret", encoding="utf-8")
    (tmp_path / "workspace" / "link.txt").symlink_to(tmp_path / "outside.txt")
    tool = FileReadTool(root=tmp_path / "workspace")
    assert "escapes the authorized root" in tool.execute(operation="read", path="link.txt")


def test_list_is_sorted_and_pattern_filtered(tmp_path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "c.log").write_text("c", encoding="utf-8")
    tool = FileReadTool(root=tmp_path)
    listed = tool.execute(operation="list", path=".", pattern="*.txt")
    assert listed.splitlines() == ["a.txt", "b.txt"]


def test_write_creates_parents_and_edit_replaces(tmp_path) -> None:
    tool = FileWriteTool(root=tmp_path)
    assert "Successfully wrote" in tool.execute(operation="write", path="sub/dir/file.txt", content="alpha beta")
    assert (tmp_path / "sub" / "dir" / "file.txt").read_text(encoding="utf-8") == "alpha beta"
    assert "Successfully edited" in tool.execute(
        operation="edit", path="sub/dir/file.txt", old_text="beta", new_text="gamma"
    )
    assert (tmp_path / "sub" / "dir" / "file.txt").read_text(encoding="utf-8") == "alpha gamma"


def test_edit_reports_missing_text_and_multiple_replacements(tmp_path) -> None:
    (tmp_path / "f.txt").write_text("x x", encoding="utf-8")
    tool = FileWriteTool(root=tmp_path)
    assert "not found" in tool.execute(operation="edit", path="f.txt", old_text="zzz", new_text="y")
    result = tool.execute(operation="edit", path="f.txt", old_text="x", new_text="y")
    assert result.startswith("Warning: Found 2 occurrences")
    assert (tmp_path / "f.txt").read_text(encoding="utf-8") == "y y"


def test_write_refuses_outside_root(tmp_path) -> None:
    tool = FileWriteTool(root=tmp_path / "workspace")
    assert "escapes the authorized root" in tool.execute(operation="write", path="../evil.txt", content="no")


def test_read_source_window(tmp_path) -> None:
    (tmp_path / "code.py").write_text("\n".join(f"line{i}" for i in range(1, 31)), encoding="utf-8")
    tool = ReadSourceTool(root=tmp_path, max_read_lines=10)
    window = tool.execute(path="code.py", start_line=5, max_lines=3)
    assert window == "line5\nline6\nline7"
    assert "beyond end of file" in tool.execute(path="code.py", start_line=100)
    schema_max = tool.input_schema["properties"]["max_lines"]["maximum"]
    assert schema_max == 10
