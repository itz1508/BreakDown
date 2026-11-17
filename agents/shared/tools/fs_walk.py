"""Bounded, root-safe source traversal shared by read-only capabilities.

The skip list and the escape refusals live here once. Callers choose which
suffixes they read; nothing in this module executes, writes, or interprets the
files it yields.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

SKIPPED_DIRECTORIES = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", ".transfer-quarantine"})


def _skipped(relative_parts: tuple[str, ...]) -> bool:
    return any(part in SKIPPED_DIRECTORIES or part.startswith(".pytest-") for part in relative_parts)


def iter_source_files(root: Path, scope: Path, suffixes: tuple[str, ...] = (".py",)) -> Iterator[Path]:
    """Yield ordinary in-root files with the given suffixes in stable path order.

    Directory symlinks are never traversed, file symlinks are skipped, and a
    candidate that resolves outside ``root`` raises ``ValueError`` instead of
    being read.
    """
    if not suffixes:
        raise ValueError("at least one suffix is required")
    root = root.resolve(strict=True)
    scope = scope.resolve(strict=True)
    if not scope.is_relative_to(root):
        raise ValueError("source scope escapes repository root")
    matches: set[Path] = set()
    for suffix in suffixes:
        for path in scope.rglob(f"*{suffix}"):
            if _skipped(path.relative_to(root).parts):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            if not path.resolve(strict=True).is_relative_to(root):
                raise ValueError("source escapes repository root")
            matches.add(path)
    yield from sorted(matches)
