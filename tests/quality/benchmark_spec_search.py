"""Labeled Spec Search benchmark: recall@k and MRR over a fixture repository.

Offline only. The real search implementation produces every hit; the labels are
predefined and are never derived from search output. Prints one JSON object and
exits nonzero when any case misses its label.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agents.skills.spec_search.spec_searching import SpecQuery, search

FILES = {
    "src/bucket.py": "class TokenBucket:\n    pass\n",
    "src/window.py": "def sliding_window() -> None:\n    pass\n",
    "conf/app.yaml": "rate_limit: TokenBucket\n",
    "docs/spec.md": "The TokenBucket pattern is described here.\n",
    "docs/runbook.md": "Run the migration before restart.\n",
    "agent/host/store.py": "def checkpoint_cas(revision, state):\n    pass\n",
    "agent/shared/canon.py": "def digest_raw(data):\n    pass\n",
    "docs/policy.md": "Retrieval must stay read-only.\n",
    "agent/skills/planner/plan.yaml": "pipeline_id: planner.plan\n",
}

CASES: tuple[tuple[str, str | None], ...] = (
    ("TokenBucket", "src/bucket.py"),
    ("sliding_window", "src/window.py"),
    ("rate_limit", "conf/app.yaml"),
    ("TokenBucket pattern", "docs/spec.md"),
    ("migration", "docs/runbook.md"),
    ("checkpoint_cas", "agent/host/store.py"),
    ("digest_raw", "agent/shared/canon.py"),
    ("read-only", "docs/policy.md"),
    ("pipeline_id", "agent/skills/planner/plan.yaml"),
    ("window", "src/window.py"),
    ("cas", "agent/host/store.py"),
    ("definitely_absent_term", None),
)


def build_repo(root: Path) -> Path:
    repo = root / "repo"
    for name, content in FILES.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return repo


def main() -> int:
    labels = {expected for _, expected in CASES if expected is not None}
    missing_labels = sorted(label for label in labels if label not in FILES)
    if missing_labels:
        raise SystemExit(f"benchmark labels reference unknown files: {missing_labels}")

    with tempfile.TemporaryDirectory(prefix="spec-search-bench-") as folder:
        repo = build_repo(Path(folder))
        results = []
        for term, expected in CASES:
            paths = [hit.path for hit in search(repo, SpecQuery(terms=(term,))).hits]
            hit = next((path for path in paths if path == expected), None)
            rank = paths.index(hit) + 1 if hit is not None else None
            empty_expected = expected is None
            results.append(
                {
                    "term": term,
                    "expected": expected,
                    "top": paths[0] if paths else None,
                    "rank": rank,
                    "matched": (not paths) if empty_expected else rank is not None,
                }
            )

    total = len(results)
    recall_at_1 = (
        sum(1 for item in results if item["rank"] == 1 or (item["expected"] is None and not item["top"])) / total
    )
    recall_at_3 = (
        sum(
            1
            for item in results
            if (item["rank"] is not None and item["rank"] <= 3) or (item["expected"] is None and not item["top"])
        )
        / total
    )
    ranked = [item for item in results if item["expected"] is not None]
    reciprocal = [1 / item["rank"] if item["rank"] else 0.0 for item in ranked]
    mismatches = [item for item in results if not item["matched"]]
    print(
        json.dumps(
            {
                "evaluation": "fixture_only_not_semantic_retrieval",
                "fixtures": total,
                "ranked_cases": len(ranked),
                "recall_at_1": round(recall_at_1, 3),
                "recall_at_3": round(recall_at_3, 3),
                "mrr": round(sum(reciprocal) / len(ranked), 3),
                "mismatches": mismatches,
            },
            sort_keys=True,
        )
    )
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
