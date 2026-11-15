"""Trusted allowlist for optional sandbox integrations; no arbitrary module names."""

from __future__ import annotations

from importlib import import_module
from typing import Any, cast

from ..backend import SandboxBackend

_BACKENDS = {"modal": ("oneshot_sandbox.integrations.modal", "ModalRuntime")}


def backend_names() -> tuple[str, ...]:
    return tuple(sorted(_BACKENDS))


def create_backend(name: str, *, app_name: str, create_app: bool = False) -> SandboxBackend:
    """Resolve only a registered provider and check its adapter configuration."""
    if name not in _BACKENDS:
        raise ValueError("unregistered sandbox backend")
    module_name, class_name = _BACKENDS[name]
    module = import_module(module_name)
    module.verify_backend_credentials()
    backend_cls: Any = getattr(module, class_name)
    return cast(SandboxBackend, backend_cls(app_name, create_app=create_app))
