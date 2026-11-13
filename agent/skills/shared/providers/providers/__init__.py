"""OneShot provider adapters — provider-neutral model access."""

from agent.skills.shared.providers.providers.base import (
    CapabilityDescriptor,
    ProviderAdapter,
    ProviderError,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    UnsupportedCapabilityError,
    UnsupportedProviderError,
)
from agent.skills.shared.providers.providers.echo import EchoProvider
from agent.skills.shared.providers.providers.registry import ProviderRegistry

__all__ = [
    "CapabilityDescriptor",
    "EchoProvider",
    "ProviderAdapter",
    "ProviderError",
    "ProviderEvent",
    "ProviderRegistry",
    "ProviderRequest",
    "ProviderResult",
    "UnsupportedCapabilityError",
    "UnsupportedProviderError",
]
