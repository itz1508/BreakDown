"""Breakdown startup doctor: dependency-free preflight, uv sync, then runtime diagnostics."""

from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def check(name: str, status: str, detail: str) -> None:
    print(f"{name}: {status} - {detail}", flush=True)


def preflight(root: Path) -> str | None:
    """Run before installing or importing any project dependencies."""
    check("python", "passed" if sys.version_info >= (3, 11) else "blocked", platform.python_version())
    if sys.version_info < (3, 11):  # noqa: UP036 -- doctor also runs before uv installs dependencies
        return None
    for name in ("pyproject.toml", "uv.lock", "config/config.yaml"):
        if not (root / name).is_file():
            check("project_file", "blocked", f"Missing {name}")
            return None
        check("project_file", "passed", name)
    uv = shutil.which("uv")
    check("uv", "passed" if uv else "blocked", uv or "uv executable not found")
    return uv


def runtime_diagnostics(root: Path) -> int:
    """Run only after dependency sync, under the uv-managed project interpreter."""
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from agent.skills.shared.host.loaders import load_app_config, load_selected_provider

        app = load_app_config(root / "config/config.yaml")
        provider = load_selected_provider(app, root)
    except (ImportError, OSError, ValueError, RuntimeError) as exc:
        check("runtime_config", "blocked", f"{type(exc).__name__}: {exc}")
        return 1

    check("pydantic", "passed" if importlib.util.find_spec("pydantic") else "blocked", "import")
    check("provider_sdk", "passed" if importlib.util.find_spec(provider.sdk) else "blocked", provider.sdk)
    check("provider_credentials", "passed" if os.getenv(provider.api_key_env) else "not_run", provider.api_key_env)
    state = os.getenv(app.state.root_env)
    if not state:
        check("state_root", "blocked", app.state.root_env)
        return 1
    target = Path(state)
    try:
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target, delete=True) as fh:
            fh.write(b"probe")
            fh.flush()
            os.fsync(fh.fileno())
        with sqlite3.connect(target / "doctor.db") as db:
            db.execute("create table if not exists probe(id integer)")
            db.commit()
        check("state_root", "passed", str(target))
    except (OSError, sqlite3.Error) as exc:
        check("state_root", "blocked", str(exc))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--runtime-check", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()

    if args.runtime_check:
        return runtime_diagnostics(root)

    uv = preflight(root)
    if uv is None:
        return 1

    command = [uv, "sync", "--locked"]
    try:
        subprocess.run([*command, "--dry-run"], cwd=root, check=True)
        subprocess.run(command, cwd=root, check=True)
        subprocess.run([*command, "--check"], cwd=root, check=True)
        subprocess.run(
            [uv, "run", "--no-sync", "python", str(Path(__file__).resolve()), "--runtime-check", "--root", str(root)],
            cwd=root,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        check("startup", "blocked", f"command exited with status {exc.returncode}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
