"""Minimal stub for rfc8785 (JSON Canonicalization Scheme).

The real library implements RFC 8785 canonical JSON. This stub provides
the canonicalize function used by the serialization module.
"""
import json

def canonicalize(obj) -> str:
    """Produce canonical JSON per RFC 8785 (simplified)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
