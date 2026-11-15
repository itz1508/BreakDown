"""Startup doctor must validate prerequisites before attempting dependency changes."""

from __future__ import annotations

import subprocess
import sys

from scripts import doctor


def test_missing_lock_blocks_sync(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.1'\n")
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--root", str(tmp_path)])

    def must_not_run(*args, **kwargs):
        raise AssertionError("uv must not run before doctor preflight passes")

    monkeypatch.setattr(doctor.subprocess, "run", must_not_run)
    assert doctor.main() == 1


def test_missing_uv_blocks_sync(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "uv.lock").touch()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.yaml").touch()
    monkeypatch.setattr(doctor.shutil, "which", lambda command: None)
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--root", str(tmp_path)])

    def must_not_run(*args, **kwargs):
        raise AssertionError("sync must not execute without uv")

    monkeypatch.setattr(doctor.subprocess, "run", must_not_run)
    assert doctor.main() == 1


def test_preflight_precedes_sync_and_runtime_diagnostics(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "uv.lock").touch()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.yaml").touch()
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/uv")
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--root", str(tmp_path)])
    calls = []

    def record(command, *, cwd, check):
        assert cwd == tmp_path
        assert check is True
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(doctor.subprocess, "run", record)
    assert doctor.main() == 0
    assert calls[0] == ["/usr/bin/uv", "sync", "--locked", "--dry-run"]
    assert calls[1] == ["/usr/bin/uv", "sync", "--locked"]
    assert calls[2] == ["/usr/bin/uv", "sync", "--locked", "--check"]
    assert calls[3][:4] == ["/usr/bin/uv", "run", "--no-sync", "python"]
    assert "--runtime-check" in calls[3]


def test_failed_sync_blocks_runtime_diagnostics(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "uv.lock").touch()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.yaml").touch()
    monkeypatch.setattr(doctor.shutil, "which", lambda command: "/usr/bin/uv")
    monkeypatch.setattr(sys, "argv", ["doctor.py", "--root", str(tmp_path)])
    calls = []

    def fail_on_sync(command, *, cwd, check):
        calls.append(command)
        if "--dry-run" not in command:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(doctor.subprocess, "run", fail_on_sync)
    assert doctor.main() == 1
    assert len(calls) == 2
