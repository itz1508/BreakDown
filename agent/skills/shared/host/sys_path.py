"""Host path containment. This module does not grant authorization."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class PathSafetyError(ValueError):
    """A requested filesystem path is outside an allowed root."""


def resolve_allowed_path(path: str | Path, allowed_roots: Iterable[str | Path]) -> Path:
    """Resolve symlinks and permit only paths contained by an allowed root.

    This preserves the existing Host containment semantics; the caller must
    separately verify its capability grant and any action/preimage binding.
    """
    roots = tuple(Path(root).resolve() for root in allowed_roots)
    if not roots:
        raise PathSafetyError("no allowed roots configured")
    resolved = Path(path).resolve()
    if any(resolved.is_relative_to(root) for root in roots):
        return resolved
    raise PathSafetyError(f"path outside allowed roots: {path}")
