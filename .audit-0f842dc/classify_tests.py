"""Classify tests for generation retirement.

Retire: any test module importing a retired prefix
(agent., contracts., system.host., mvp., app.).
Keep: everything else. Output lists for review.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path("tests")
PATTERN = re.compile(r"^\s*(?:from|import)\s+(agent\b|contracts\b|system\.host\b|mvp\b|app\b)", re.MULTILINE)

retire: list[str] = []
keep: list[str] = []
for path in sorted(ROOT.rglob("test_*.py")):
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = PATTERN.findall(text)
    target = retire if hits else keep
    target.append(f"{path.as_posix()}  # imports: {sorted(set(hits)) or 'none'}")

out = pathlib.Path(".audit-0f842dc/test_classification.txt")
out.write_text(
    "== RETIRE (import retired prefixes) ==\n" + "\n".join(retire) + "\n\n== KEEP ==\n" + "\n".join(keep) + "\n",
    encoding="utf-8",
)
print(f"retire={len(retire)} keep={len(keep)}")
conftest = [p.as_posix() for p in ROOT.rglob("conftest.py")]
print("conftest files:", conftest)
