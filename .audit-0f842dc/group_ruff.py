"""Group ruff findings by top-level directory and rule code."""

from __future__ import annotations

import collections
import pathlib
import re

report = pathlib.Path(".audit-0f842dc/ruff_full.txt")
by_dir: collections.Counter[str] = collections.Counter()
by_code: collections.Counter[str] = collections.Counter()
for line in report.read_text(encoding="utf-8", errors="replace").splitlines():
    match = re.match(r"^\s*--> ([^:]+):(\d+):\d+", line)
    if match:
        top = match.group(1).replace("\\", "/").split("/", 1)[0]
        by_dir[top] += 1
        by_code["total"] += 1

out = pathlib.Path(".audit-0f842dc/ruff_grouped.txt")
lines = ["== by directory =="]
lines += [f"{k}: {v}" for k, v in by_dir.most_common()]
lines.append("== by code ==")
lines += [f"{k}: {v}" for k, v in by_code.most_common(12)]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

