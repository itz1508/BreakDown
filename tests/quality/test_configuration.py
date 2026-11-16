"""Installed provider configuration loads, resolves and builds without network.

Only the shipped YAML and an injected stub client are used, so this needs no API
key, no outbound call and no model access. It replaces the deleted unit layer's
"installed provider selection" check.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.skills.shared.contracts.workflow.system.provider import ProviderProtocol
from agents.skills.shared.providers.provider_config import (
    ProviderConfigurationError,
    load_provider_config,
    resolve_api_key,
    resolve_model,
)

META_YAML = """\
provider_id: meta
protocol: openai_compatible
sdk: openai
api_key_env: MODEL_API_KEY
base_url: https://api.meta.ai/v1
base_url_env: META_MODEL_BASE_URL
model: muse-spark-1.3
model_env: META_MODEL_ID
timeout_seconds: 60
max_retries: 0
capabilities:
  chat: required
  streaming: required
  tool_calling: required
  structured_output: required
  error_handling: required
"""


@pytest.fixture
def meta_config_path(tmp_path: Path) -> Path:
    path = tmp_path / "meta.yaml"
    path.write_text(META_YAML, encoding="utf-8")
    return path


def test_shipped_provider_config_loads(meta_config_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("META_MODEL_ID", raising=False)
    config = load_provider_config(meta_config_path)
    assert config.provider_id == "meta"
    assert config.protocol is ProviderProtocol.OPENAI_COMPATIBLE
    assert config.api_key_env == "MODEL_API_KEY"
    assert resolve_model(config) == config.model


def test_model_environment_override_wins(meta_config_path: Path, monkeypatch) -> None:
    config = load_provider_config(meta_config_path)
    monkeypatch.setenv("META_MODEL_ID", "override-model")
    assert resolve_model(config) == "override-model"


def test_missing_api_key_fails_closed(meta_config_path: Path, monkeypatch) -> None:
    config = load_provider_config(meta_config_path)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(ProviderConfigurationError, match="Missing MODEL_API_KEY"):
        resolve_api_key(config)


def test_config_without_model_or_environment_is_rejected(tmp_path) -> None:
    path = tmp_path / "provider.yaml"
    path.write_text("provider_id: broken\nsdk: openai\napi_key_env: KEY\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="model or model_env"):
        load_provider_config(path)
