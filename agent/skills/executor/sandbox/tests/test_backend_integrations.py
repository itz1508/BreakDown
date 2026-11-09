"""Provider neutrality: core import does not select Modal; registry fails closed."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

from oneshot_sandbox.integrations import backend_names, create_backend


def test_importing_core_does_not_load_modal_sdk() -> None:
    code = "import sys; import oneshot_sandbox.runner; assert 'modal' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True, env=os.environ.copy())


def test_backend_registry_only_lists_explicit_integrations() -> None:
    assert backend_names() == ("modal",)


def test_unknown_backend_is_denied() -> None:
    with pytest.raises(ValueError, match="unregistered"):
        create_backend("arbitrary.module:InjectedBackend", app_name="no")


def test_modal_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="credentials absent"):
        create_backend("modal", app_name="existing-app")
