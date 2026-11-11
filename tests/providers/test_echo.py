"""Test echo provider generate."""

from system.host.providers.base import ProviderRequest
from system.host.providers.echo import EchoProvider


def test_echo_generate():
    p = EchoProvider()
    q = ProviderRequest(run_id="r", prompt="hello")
    result = p.generate(q)
    assert result.content.startswith("echo:")
    assert result.provider == "echo"
