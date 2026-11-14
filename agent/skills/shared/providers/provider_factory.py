"""Factory for building provider adapters from configuration."""

from __future__ import annotations

from typing import Any

from agent.skills.shared.contracts.workflow.system.provider import ProviderConfig, ProviderProtocol
from agent.skills.shared.providers.providers.openai_compatible import OpenAICompatibleAdapter


def build_provider(config: ProviderConfig, client: Any | None = None) -> OpenAICompatibleAdapter:
    """Build a provider adapter from a ProviderConfig.

    Currently only the openai_compatible protocol is supported.
    """
    if config.protocol is not ProviderProtocol.OPENAI_COMPATIBLE:
        raise ValueError(f"Unsupported protocol: {config.protocol}")
    return OpenAICompatibleAdapter(config, client=client)
