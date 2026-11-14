"""Read-only specification evidence search; no stage, receipt, or effect."""

from agent.skills.spec_search.spec_searching import (
    DEFAULT_SUFFIXES,
    Skip,
    SpecHit,
    SpecQuery,
    SpecSearchError,
    SpecSearchResult,
    normalize_terms,
    scan_file,
    search,
)

__all__ = [
    "DEFAULT_SUFFIXES",
    "Skip",
    "SpecHit",
    "SpecQuery",
    "SpecSearchError",
    "SpecSearchResult",
    "normalize_terms",
    "scan_file",
    "search",
]
