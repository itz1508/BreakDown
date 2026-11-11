"""Read-only CI check: reject restoration of retired and competing Git paths."""

from __future__ import annotations

import subprocess
import sys
import unicodedata
from pathlib import Path

RETIRED_PREFIXES = (
    "mvp/", ".agents/", "deployment/modal/sandbox_v3/",
    "agent/skills/executor/sandbox/", "tests/fixtures/repo_compat/",
    "contracts/runtime/",
)
RETIRED_EXACT = frozenset({
    "conftest.py", "tests/conftest.py", "docs/workflow-test-design.md",
    "agent/draft.py", "config/workflow.yaml",
    "agent/skills/researcher/tools/search.yaml", "modal_app.py", "demo_app.py",
})
REJECTED_PREFIXES = (
    "agent/contracts/", "agent/runtime/", "deployment/modal/scanner/oneshot/",
)
REJECTED_EXACT = frozenset({
    "settings/config.yaml", ".github/workflows/executor-sandbox.yml",
    "agent/skills/auditor/run.py", "agent/skills/builder/run.py",
    "agent/skills/planner/run.py", "agent/skills/researcher/run.py",
})


def forbidden_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Check normalized tracked paths and detect casefold aliases."""
    blocked: set[str] = set()
    exact = {p.casefold() for p in RETIRED_EXACT | REJECTED_EXACT}
    prefixes = tuple(p.casefold() for p in RETIRED_PREFIXES + REJECTED_PREFIXES)
    seen: dict[str, str] = {}
    for original in paths:
        normalized = unicodedata.normalize("NFC", original)
        folded = normalized.casefold()
        if (
            normalized != original
            or original.startswith("/")
            or "\\" in original
            or "\x00" in original
            or ".." in original.split("/")
            or folded in exact
            or any(folded.startswith(prefix) for prefix in prefixes)
            or (folded in seen and seen[folded] != original)
        ):
            blocked.add(original)
        seen[folded] = original
    return tuple(sorted(blocked))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True,
    )
    paths = tuple(
        item.decode("utf-8", "surrogateescape")
        for item in result.stdout.split(b"\0") if item
    )
    violations = forbidden_paths(paths)
    if violations:
        print("Retired or competing tracked paths:", file=sys.stderr)
        for path in violations:
            print(f"  {path}", file=sys.stderr)
        return 1
    print(f"Non-restoration guard: {len(paths)} tracked paths accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
