"""Provider-executed server tools: declared here, executed by the provider.

Server tools have no client-side ``execute`` — the provider runs them. This
package deliberately does not hardcode provider type identifiers or API
version strings; the provider adapter maps a ServerTool's capability and
options onto its own wire format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ServerTool:
    """One provider-executed capability with caller-supplied options."""

    capability: str  # neutral id, e.g. "web_search" or "code_execution"
    options: dict[str, Any] = field(default_factory=dict)

    def declaration(self) -> dict[str, Any]:
        """Return the neutral declaration: the capability plus its options."""
        return {"server_tool": self.capability, **self.options}
