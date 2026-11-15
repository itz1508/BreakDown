"""Test config loading."""

from pathlib import Path

from system.host.loaders import load_app_config, load_selected_provider


def test_config_loads():
    app = load_app_config(Path("config/config.yaml"))
    provider = load_selected_provider(app, Path.cwd())
    assert provider.provider_id == "meta"
    assert app.security.default_deny
