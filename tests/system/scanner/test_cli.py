"""Preflight and predict tests, plus the CLI surface."""

from __future__ import annotations

import json
import subprocess
import sys

from system.scanner import scan_predict, scan_preflight


def test_preflight_detects_retired_paths_from_caller_ledger(tmp_path) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "mod.py").write_text("X = 1\n", encoding="utf-8")
    report = scan_preflight(tmp_path, retired_prefixes=("agents/",))
    assert report.verdict.value == "not_valid"
    assert any(f.detector == "retired-path" and f.path == "agents/mod.py" for f in report.findings)


def test_preflight_clean_tree_is_valid(tmp_path) -> None:
    (tmp_path / "lib.py").write_text("X = 1\n", encoding="utf-8")
    report = scan_preflight(tmp_path, retired_prefixes=("agents/",))
    assert report.verdict.value == "valid"
    assert report.findings == ()


def test_preflight_import_boundary_rule(tmp_path) -> None:
    (tmp_path / "systemlib").mkdir()
    (tmp_path / "systemlib" / "core.py").write_text("import agents.skills\n", encoding="utf-8")
    report = scan_preflight(tmp_path, boundary_rules={"systemlib/": "agents."})
    assert report.verdict.value == "not_valid"
    assert any(f.detector == "boundary-import" for f in report.findings)


def test_predict_reports_added_modified_removed(tmp_path) -> None:
    from system.scanner._types import FileEntry

    (tmp_path / "kept.py").write_text("X = 1\n", encoding="utf-8")
    first = scan_predict((), tmp_path)
    baseline = first.entries
    (tmp_path / "added.py").write_text("Y = 2\n", encoding="utf-8")
    (tmp_path / "kept.py").write_text("X = 2\n", encoding="utf-8")
    # gone.py exists only in the baseline: it was deleted after the baseline ran
    gone_entry = FileEntry("gone.py", "a" * 64, 6)
    baseline_with_gone = (*baseline, gone_entry)

    report = scan_predict(baseline_with_gone, tmp_path)
    messages = {f.path: f.message for f in report.findings}
    assert messages["added.py"] == "added since baseline"
    assert messages["gone.py"] == "removed since baseline"
    assert messages["kept.py"] == "modified since baseline"
    assert report.verdict.value == "indeterminate"


def test_predict_with_empty_baseline_is_indeterminate(tmp_path) -> None:
    (tmp_path / "a.py").write_text("X = 1\n", encoding="utf-8")
    report = scan_predict((), tmp_path)
    assert report.verdict.value == "indeterminate"
    assert any("empty baseline" in f.message for f in report.findings)


def test_cli_debug_mode_outputs_json_report(tmp_path) -> None:
    (tmp_path / "ok.py").write_text("X = 1\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "system.scanner", str(tmp_path), "--mode", "debug"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["mode"] == "debug"
    assert report["verdict"] == "valid"
    assert report["files_scanned"] == 1


def test_cli_requires_baseline_for_predict(tmp_path) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "system.scanner", str(tmp_path), "--mode", "predict"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 2
