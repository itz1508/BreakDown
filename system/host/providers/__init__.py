"""OneShot provider adapters — provider-neutral model access."""

from system.host.providers.base import (
    CapabilityDescriptor,
    ProviderAdapter,
    ProviderError,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    UnsupportedCapabilityError,
    UnsupportedProviderError,
)
from system.host.providers.echo import EchoProvider
from system.host.providers.registry import ProviderRegistry

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
