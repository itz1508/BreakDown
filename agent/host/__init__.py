"""OneShot host runtime — stores, authorization, controller, providers."""

from agent.host.storage.canonical_serialization import canonical_bytes, digest_model, digest_raw

__all__ = ["canonical_bytes", "digest_model", "digest_raw"]
