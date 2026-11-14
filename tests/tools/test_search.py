"""Repository search tool tests: matching, bounds, scope and escapes."""

from __future__ import annotations

from agents.tools.search import RepositorySearchTool


def test_finds_literal_terms_with_paths(tmp_path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("TOKEN = 'x'\nother\nTOKEN again\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("no match here\n", encoding="utf-8")
    tool = RepositorySearchTool(root=tmp_path)
    result = tool.execute(terms=["TOKEN"], max_results=10)
    assert "pkg/mod.py:1" in result
    assert "pkg/mod.py:3" in result
    assert "readme" not in result


def test_respects_max_results_and_scope(tmp_path) -> None:
    for index in range(5):
        (tmp_path / f"f{index}.txt").write_text("needle\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "s.txt").write_text("needle\n", encoding="utf-8")
    tool = RepositorySearchTool(root=tmp_path)
    limited = tool.execute(terms=["needle"], max_results=3)
    assert len(limited.splitlines()) == 3
    scoped = tool.execute(terms=["needle"], scope="sub")
    assert scoped == "sub/s.txt:1: needle"


def test_no_match_and_escape_are_reported(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("nothing\n", encoding="utf-8")
    tool = RepositorySearchTool(root=tmp_path)
    assert "No matches" in tool.execute(terms=["absent"])
    assert "escapes the authorized root" in tool.execute(terms=["x"], scope="../elsewhere")
