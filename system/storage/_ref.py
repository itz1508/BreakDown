"""Canonical system references: one string format for every kind."""

from __future__ import annotations

_KNOWN_KINDS = frozenset({"todo", "exec", "event", "output", "artifact", "receipt"})


def sys_ref(kind: str, ident: str) -> str:
    """Return the canonical reference string ``kind:ident`` for a known kind."""
    if kind not in _KNOWN_KINDS:
        raise ValueError(f"unknown reference kind: {kind!r}")
    if not ident or not isinstance(ident, str):
        raise ValueError("reference ident must be a non-empty string")
    return f"{kind}:{ident}"
