"""Deterministic, read-only specification evidence search.

Query-driven retrieval for Research and Planning: it locates declared symbols,
configuration keys and prose references, and returns the exact snippet with a
digest. It does not call a model, choose a design, write source, or issue
receipts; ranking is lexical and fully reproducible.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from agents.skills.shared.tools.fs_walk import iter_source_files
from system.storage.canonical_serialization import digest_raw

DEFAULT_SUFFIXES: tuple[str, ...] = (".py", ".md", ".yaml", ".yml", ".toml", ".json")


class SpecSearchError(ValueError):
    """Raised when a query or repository root cannot be searched as requested."""


@dataclass(frozen=True)
class SpecQuery:
    """Search request. Terms are matched literally; no model or synonym expansion."""

    terms: tuple[str, ...]
    scope: str = "."
    suffixes: tuple[str, ...] = DEFAULT_SUFFIXES
    max_results: int = 20
    max_files: int = 500
    max_file_bytes: int = 1_000_000
    context_lines: int = 2

    def __post_init__(self) -> None:
        if not any(term.strip() for term in self.terms):
            raise SpecSearchError("at least one search term required")
        if Path(self.scope).is_absolute():
            raise SpecSearchError("spec search scope must be relative to repository root")
        if not self.suffixes:
            raise SpecSearchError("at least one suffix is required")
        if self.max_results < 1 or self.max_files < 1 or self.max_file_bytes < 1:
            raise SpecSearchError("search budgets must be positive")
        if self.context_lines < 0:
            raise SpecSearchError("context_lines cannot be negative")


@dataclass(frozen=True)
class Skip:
    """A file that was intentionally not searched, with the reason."""

    path: str
    reason: str


@dataclass(frozen=True)
class SpecHit:
    path: str
    line: int
    snippet: str
    snippet_digest: str
    score: int
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class SpecSearchResult:
    query: SpecQuery
    hits: tuple[SpecHit, ...]
    files_scanned: int
    skipped: tuple[Skip, ...]
    truncated: bool
    truncated_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_terms(terms: Iterable[str]) -> tuple[str, ...]:
    """Strip and de-duplicate terms while preserving the caller's order."""
    normalized: list[str] = []
    for raw in terms:
        term = raw.strip()
        if term and term not in normalized:
            normalized.append(term)
    if not normalized:
        raise SpecSearchError("at least one search term required")
    return tuple(normalized)


def _strength(line: str, term: str) -> int:
    """3 = whole word, 2 = exact substring, 1 = case-insensitive, 0 = no match."""
    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", line):
        return 3
    if term in line:
        return 2
    if term.lower() in line.lower():
        return 1
    return 0


def _is_declaration(line: str, term: str) -> bool:
    """A match on a declared symbol outranks the same match inside prose."""
    return bool(re.match(rf"\s*(?:class|def|async\s+def)\s+{re.escape(term)}\b", line))


def scan_file(root: Path, path: Path, terms: Sequence[str], query: SpecQuery) -> tuple[list[SpecHit], str | None]:
    """Return one file's hits, or the reason it was skipped."""
    if path.stat().st_size > query.max_file_bytes:
        return [], "size"
    data = path.read_bytes()
    if len(data) > query.max_file_bytes:
        return [], "size"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [], "decode_error"

    relative = path.relative_to(root).as_posix()
    lines = text.splitlines()
    hits: list[SpecHit] = []
    for index, line in enumerate(lines):
        matched = tuple(term for term in terms if _strength(line, term) > 0)
        if not matched:
            continue
        score = max(_strength(line, term) + int(_is_declaration(line, term)) for term in matched)
        start = max(0, index - query.context_lines)
        stop = min(len(lines), index + query.context_lines + 1)
        snippet = "\n".join(lines[start:stop])
        hits.append(
            SpecHit(
                path=relative,
                line=index + 1,
                snippet=snippet,
                snippet_digest=digest_raw(snippet.encode("utf-8")),
                score=score,
                matched_terms=matched,
            )
        )
    return hits, None


def search(root: Path, query: SpecQuery) -> SpecSearchResult:
    """Search one root. Refuses anything it cannot read rather than guessing."""
    if not root.exists() or not root.is_dir():
        raise SpecSearchError("repository root must be a directory")
    root = root.resolve(strict=True)
    scope = (root / query.scope).resolve()
    if not scope.is_dir():
        raise SpecSearchError("spec search scope must be a directory")
    if not scope.is_relative_to(root):
        raise SpecSearchError("spec search scope escapes repository root")

    terms = normalize_terms(query.terms)
    hits: list[SpecHit] = []
    skipped: list[Skip] = []
    files_scanned = 0
    truncated_reason: str | None = None
    for path in iter_source_files(root, scope, query.suffixes):
        if files_scanned >= query.max_files:
            truncated_reason = "file_budget"
            break
        files_scanned += 1
        file_hits, reason = scan_file(root, path, terms, query)
        if reason is not None:
            skipped.append(Skip(path=path.relative_to(root).as_posix(), reason=reason))
        hits.extend(file_hits)

    ordered = sorted(hits, key=lambda hit: (-hit.score, -len(hit.matched_terms), hit.path, hit.line))
    if len(ordered) > query.max_results:
        ordered = ordered[: query.max_results]
        truncated_reason = "result_budget"
    return SpecSearchResult(
        query=query,
        hits=tuple(ordered),
        files_scanned=files_scanned,
        skipped=tuple(skipped),
        truncated=truncated_reason is not None,
        truncated_reason=truncated_reason,
    )
