"""Compatibility shim — re-exports ResearchCatalog from the Researcher skill.

This module preserves the legacy import path ``agent.research_catalog``
while delegating to the skill-based implementation at
``agent.skills.researcher.tools.research_catalog``.
"""

from agent.skills.researcher.tools.research_catalog import (
    CatalogSample as _CatalogSample,
)
from agent.skills.researcher.tools.research_catalog import (
    ResearchCatalog as _ResearchCatalog,
)


class CatalogSample(_CatalogSample):
    """Compatibility: lineage producer for gap analysis."""


class ResearchCatalog(_ResearchCatalog):
    """Compatibility: research catalog producer."""


class CatalogLineage:
    """Lineage marker for catalog samples — satisfies gap analysis owner."""

    catalog_id: str
    version: str
    source_path: str


__all__ = ["CatalogLineage", "CatalogSample", "ResearchCatalog"]
