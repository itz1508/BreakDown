"""Installed provider configuration loads, resolves and builds without network.

Only the shipped YAML and an injected stub client are used, so this needs no API
key, no outbound call and no model access. It replaces the deleted unit layer's
"installed provider selection" check.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent.skills.shared.contracts.workflow.system.provider import ProviderProtocol
from agent.skills.shared.providers.provider_config import (
    ProviderConfigurationError,
    load_provider_config,
    resolve_api_key,
    resolve_model,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
META = REPO_ROOT / "config" / "providers" / "meta.yaml"


def test_shipped_provider_config_loads(monkeypatch) -> None:
    monkeypatch.delenv("META_MODEL_ID", raising=False)
    config = load_provider_config(META)
    assert config.provider_id == "meta"
    assert config.protocol is ProviderProtocol.OPENAI_COMPATIBLE
    assert config.api_key_env == "MODEL_API_KEY"
    assert resolve_model(config) == config.model


def test_model_environment_override_wins(monkeypatch) -> None:
    config = load_provider_config(META)
    monkeypatch.setenv("META_MODEL_ID", "override-model")
    assert resolve_model(config) == "override-model"


def test_missing_api_key_fails_closed(monkeypatch) -> None:
    config = load_provider_config(META)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(ProviderConfigurationError, match="Missing MODEL_API_KEY"):
        resolve_api_key(config)


def test_config_without_model_or_environment_is_rejected(tmp_path) -> None:
    path = tmp_path / "provider.yaml"
    path.write_text("provider_id: broken\nsdk: openai\napi_key_env: KEY\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="model or model_env"):
        load_provider_config(path)
