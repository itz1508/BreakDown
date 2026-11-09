"""Compatibility shim — re-exports ResearchCatalog from the Researcher skill.

This module preserves the legacy import path ``agent.research_catalog``
while delegating to the skill-based implementation at
``agent.skills.researcher.tools.research_catalog``.
"""

from agent.skills.researcher.tools.research_catalog import (
    CatalogSample,
    ResearchCatalog,
)

__all__ = ["CatalogSample", "ResearchCatalog"]
