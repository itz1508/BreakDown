"""Spec Search returns ranked, digest-bound evidence from a real repository.

Every test builds a temporary repository on disk; nothing is mocked. Skips and
truncation are asserted because silent omission is the failure this capability
must not have.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agents.skills.spec_search.spec_searching import SpecQuery, SpecSearchError, search
from system.storage.canonical_serialization import digest_raw

pytestmark = pytest.mark.e2e

ALPHA = '''"""Token bucket implementation."""


class TokenBucket:
    """Rate limiter."""

    def refill(self) -> None:
        """Refill tokens."""
'''

BETA = """# TODO: replace TokenBucket with a sliding window


def helper() -> None:
    return None
"""


def make_repo(tmp_path: Path) -> Path:
    """Repository with a declaration, a comment, prose, config and two unusable files."""
    repo = tmp_path / "repo"
    for directory in ("src", "docs", "conf", "data"):
        (repo / directory).mkdir(parents=True)
    (repo / "src" / "alpha.py").write_text(ALPHA, encoding="utf-8")
    (repo / "src" / "beta.py").write_text(BETA, encoding="utf-8")
    (repo / "docs" / "spec.md").write_text("The TokenBucket pattern is described here.\n", encoding="utf-8")
    (repo / "conf" / "app.yaml").write_text("rate_limit: TokenBucket\n", encoding="utf-8")
    (repo / "data" / "broken.md").write_bytes(b"\xff\xfe\x00not utf-8")
    (repo / "data" / "large.py").write_text("#" * 2000 + "\n", encoding="utf-8")
    return repo


def test_declaration_outranks_prose_and_digest_matches(tmp_path) -> None:
    result = search(make_repo(tmp_path), SpecQuery(terms=("TokenBucket",)))

    top = result.hits[0]
    assert top.path == "src/alpha.py"
    assert top.line == 4
    assert top.score == 4
    assert top.snippet_digest == digest_raw(top.snippet.encode("utf-8"))

    prose = next(hit for hit in result.hits if hit.path == "docs/spec.md")
    assert prose.score == 3
    assert top.score > prose.score


def test_budgets_are_reported_not_silent(tmp_path) -> None:
    repo = make_repo(tmp_path)

    limited = search(repo, SpecQuery(terms=("TokenBucket",), max_results=1))
    assert len(limited.hits) == 1
    assert limited.truncated is True
    assert limited.truncated_reason == "result_budget"

    file_limited = search(repo, SpecQuery(terms=("TokenBucket",), max_files=1))
    assert file_limited.files_scanned == 1
    assert file_limited.truncated is True
    assert file_limited.truncated_reason == "file_budget"


def test_unusable_files_are_reported_with_reasons(tmp_path) -> None:
    result = search(make_repo(tmp_path), SpecQuery(terms=("TokenBucket",), max_file_bytes=1024))
    reasons = {skip.path: skip.reason for skip in result.skipped}
    assert reasons["data/large.py"] == "size"
    assert reasons["data/broken.md"] == "decode_error"


def test_scope_and_budget_misuse_is_refused(tmp_path) -> None:
    repo = make_repo(tmp_path)
    with pytest.raises(SpecSearchError, match="escapes repository root"):
        search(repo, SpecQuery(terms=("TokenBucket",), scope="../"))
    with pytest.raises(SpecSearchError, match="must be relative"):
        SpecQuery(terms=("x",), scope=str(tmp_path))
    with pytest.raises(SpecSearchError, match="repository root must be a directory"):
        search(tmp_path / "missing", SpecQuery(terms=("x",)))
    with pytest.raises(SpecSearchError, match="at least one search term"):
        SpecQuery(terms=("   ",))
    with pytest.raises(SpecSearchError, match="budgets must be positive"):
        SpecQuery(terms=("x",), max_results=0)


def test_symlinked_source_is_skipped(tmp_path) -> None:
    repo = make_repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("class TokenBucket:\n    pass\n", encoding="utf-8")
    try:
        os.symlink(outside, repo / "src" / "linked.py")
    except OSError:
        pytest.skip("symlink creation is not permitted on this platform")

    result = search(repo, SpecQuery(terms=("TokenBucket",)))
    assert all(hit.path != "src/linked.py" for hit in result.hits)
    assert all(skip.path != "src/linked.py" for skip in result.skipped)


def test_output_is_stable_across_runs(tmp_path) -> None:
    repo = make_repo(tmp_path)
    query = SpecQuery(terms=("TokenBucket", " TokenBucket ", "read-only"))
    first = json.dumps(search(repo, query).to_dict(), sort_keys=True)
    second = json.dumps(search(repo, query).to_dict(), sort_keys=True)

    assert first == second
    payload = json.loads(first)
    assert payload["query"]["terms"] == ["TokenBucket", " TokenBucket ", "read-only"]
    assert payload["hits"]
