"""Check literal internal Python import targets without importing project modules."""

from __future__ import annotations

import ast
from pathlib import Path

from agent.skills.planner.tools.core import Finding, evidence


def scan_contracts(root: Path, scope: Path) -> list[Finding]:
    """Scan for internal import targets that are not present as modules."""
    findings: list[Finding] = []
    for path in sorted(scope.rglob("*.py")):
        if any(
            part in {".git", ".venv", "venv", "node_modules", "__pycache__"} for part in path.relative_to(root).parts
        ):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names: tuple[str, ...]
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = (node.module,)
            elif isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            else:
                continue
            for name in names:
                if not name.startswith(("agent.", "mvp.")):
                    continue
                if not (root / name.split(".")[0]).is_dir():
                    continue
                rel = root.joinpath(*name.split("."))
                if not rel.with_suffix(".py").is_file() and not (rel / "__init__.py").is_file():
                    findings.append(
                        evidence(
                            root,
                            path,
                            node.lineno,
                            "INTERNAL_IMPORT_MISSING",
                            "contracts",
                            "high",
                            f"Internal import target {name!r} is not present as a Python module or package.",
                        )
                    )
    return findings
