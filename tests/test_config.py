"""Test config loading."""

from pathlib import Path

from agent.skills.shared.host.loaders import load_app_config, load_selected_provider


def test_config_loads():
    app = load_app_config(Path("config/config.yaml"))
    provider = load_selected_provider(app, Path.cwd())
    assert provider.provider_id == "meta"
    assert app.security.default_deny


def test_config_profile_is_credential_free_and_versioned() -> None:
    app = load_app_config(Path("config/config.yaml"))
    assert app.provider.profile == "config/providers/meta.yaml"
    provider = load_selected_provider(app, Path.cwd())
    assert provider.provider_id == "meta"
    assert provider.sdk == "openai"
    assert provider.model == "muse-spark-1.3"
    assert provider.api_key_env == "MODEL_API_KEY"
    assert provider.base_url == "https://api.meta.ai/v1"
    assert not provider.model_dump().get("api_key")
