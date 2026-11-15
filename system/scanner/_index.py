"""Deterministic, read-only repository index.

``backend_repo`` walks a target directory in sorted order, hashes every
regular file, and reports what it could not read. It never imports or
executes anything it walks, never writes, and produces the same output for
the same tree.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from system.scanner._types import FileEntry

DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".oneshot-state",
    }
)
DEFAULT_MAX_FILE_BYTES = 1_000_000


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_excluded(relative_parts: tuple[str, ...], excluded_dirs: frozenset[str]) -> bool:
    return any(part in excluded_dirs for part in relative_parts)


def backend_repo(
    target: str | Path,
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
) -> dict[str, Any]:
    """Index the target tree deterministically.

    Returns a dict with:
    - ``entries``: sorted tuple of FileEntry (posix relative path, sha256, size)
    - ``manifest_hash``: sha256 over the entry list (the candidate identity)
    - ``files_scanned``: number of indexed files
    - ``unreadable``: files that could not be read (drives incomplete outcome)
    - ``oversized``: files skipped for exceeding the size bound
    - ``scan_root``: the resolved absolute target path
    """
    root = Path(target)
    if not root.is_dir():
        raise NotADirectoryError(f"scan target is not a directory: {root}")
    root = root.resolve()

    entries: list[FileEntry] = []
    unreadable: list[str] = []
    oversized: list[str] = []
    candidates: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _is_excluded(relative.parts, excluded_dirs):
            continue
        candidates.append((relative.as_posix(), path))

    for posix_path, path in sorted(candidates):
        try:
            size = path.stat().st_size
            if size > max_file_bytes:
                oversized.append(posix_path)
                continue
            entries.append(FileEntry(relative_path=posix_path, sha256=_hash_file(path), size_bytes=size))
        except OSError:
            unreadable.append(posix_path)

    entries.sort(key=lambda e: e.relative_path)
    manifest_hash = (
        hashlib.sha256(
            "\n".join(f"{entry.relative_path}:{entry.sha256}" for entry in entries).encode("utf-8")
        ).hexdigest()
        if entries
        else None
    )
    return {
        "entries": tuple(entries),
        "manifest_hash": manifest_hash,
        "files_scanned": len(entries),
        "unreadable": tuple(sorted(unreadable)),
        "oversized": tuple(sorted(oversized)),
        "scan_root": str(root),
    }
