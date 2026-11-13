"""OneShot provider adapters — provider-neutral model access."""

from agent.host.providers.backends.base import (
    CapabilityDescriptor,
    ProviderAdapter,
    ProviderError,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    UnsupportedCapabilityError,
    UnsupportedProviderError,
)
from agent.host.providers.backends.echo import EchoProvider
from agent.host.providers.backends.registry import ProviderRegistry

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
