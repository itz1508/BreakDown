"""Scanner engine tests: determinism, read-only guarantees, escape refusal."""

from __future__ import annotations

from pathlib import Path

from system.scanner import backend_repo, scan_debug


def make_tree(root: Path) -> None:
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "pkg" / "dupe_a.py").write_text("def go():\n    return 1\n", encoding="utf-8")
    (root / "pkg" / "dupe_b.py").write_text("def go():\n    return 1\n", encoding="utf-8")
    (root / "readme.md").write_text("readme", encoding="utf-8")


def test_determinism_same_tree_byte_identical(tmp_path) -> None:
    make_tree(tmp_path)
    first = scan_debug(tmp_path)
    second = scan_debug(tmp_path)
    assert first.to_dict() == second.to_dict()
    assert first.manifest_hash == second.manifest_hash


def test_empty_repository_is_never_valid(tmp_path) -> None:
    report = scan_debug(tmp_path)
    assert report.files_scanned == 0
    assert report.verdict.value == "not_valid"
    assert any("zero files scanned" in f.message for f in report.findings)


def test_syntax_error_reported_with_exact_location(tmp_path) -> None:
    (tmp_path / "broken.py").write_text("def f(:\n", encoding="utf-8")
    report = scan_debug(tmp_path)
    assert report.outcome.value == "incomplete"
    assert report.verdict.value == "not_valid"
    syntax = [f for f in report.findings if f.detector == "syntax-error"]
    assert len(syntax) == 1
    assert syntax[0].path == "broken.py"
    assert syntax[0].line == 1


def test_duplicate_candidate_is_diagnostic_not_blocking(tmp_path) -> None:
    make_tree(tmp_path)
    report = scan_debug(tmp_path)
    dupes = [f for f in report.findings if f.detector == "duplicate-candidate"]
    assert len(dupes) == 1
    assert dupes[0].severity == "diagnostic"
    assert dupes[0].confidence == "medium"
    assert report.verdict.value == "valid"


def test_import_sentinel_never_executes_scanned_code(tmp_path) -> None:
    marker = tmp_path / "marker.txt"
    (tmp_path / "boom.py").write_text(
        f"from pathlib import Path\nPath(r'{marker}').write_text('imported')\n"
        "raise RuntimeError('scanned code was imported')\n",
        encoding="utf-8",
    )
    report = scan_debug(tmp_path)
    assert report.files_scanned == 1
    assert not marker.exists()


def test_escapes_and_junk_dirs(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "junk.cpython-311.pyc").write_bytes(b"\x00\x01")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git", encoding="utf-8")
    index = backend_repo(tmp_path)
    paths = [entry.relative_path for entry in index["entries"]]
    assert paths == ["src/ok.py"]


def test_non_utf8_file_is_indexed_not_crashed(tmp_path) -> None:
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00\x01")
    report = scan_debug(tmp_path)
    assert report.files_scanned == 1


def test_missing_target_is_blocked(tmp_path) -> None:
    report = scan_debug(tmp_path / "nope")
    assert report.outcome.value == "blocked"
    assert report.verdict.value == "indeterminate"


def test_oversized_file_reported(tmp_path) -> None:
    (tmp_path / "big.txt").write_text("x" * 100, encoding="utf-8")
    report = scan_debug(tmp_path, max_file_bytes=10)
    assert report.files_scanned == 0
    assert any("big.txt" in getattr(f, "path", "") for f in report.findings) or report.outcome.value == "incomplete"
