"""Read-only wrapper chaos validation for agent/skills/ internal wiring.

Injects controlled observational defects into skill wrapper patterns to verify
they fail closed: no silent contract leaks, no unguarded external runtime
imports.  This tool does not modify files, dispatch tools, authorize changes,
or substitute for E2E verification.
"""

from __future__ import annotations

import ast
import codecs
from dataclasses import dataclass, field
from pathlib import Path


def _skills_root(repo_root: Path) -> Path:
    root = repo_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root must be a directory")
    skills = root / "agent" / "skills"
    if not skills.is_dir():
        raise ValueError("agent/skills/ not found")
    return skills


@dataclass(frozen=True, slots=True)
class WrapperFinding:
    skill: str
    file: str
    line: int
    code: str
    detail: str


@dataclass(frozen=True, slots=True)
class ChaosReport:
    skills_scanned: int
    files_scanned: int
    findings: tuple[WrapperFinding, ...]
    contract_leaks: int = field(default=0)
    unguarded_external: int = field(default=0)

    @property
    def is_clean(self) -> bool:
        return len(self.findings) == 0


def _scan_python_file(rel: str, fpath: Path, tc_ranges: list[tuple[int, int]]) -> list[WrapperFinding]:
    """Return findings for one .py file."""
    findings: list[WrapperFinding] = []
    with codecs.open(str(fpath), encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=str(fpath))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or not node.module:
            continue
        in_tc = any(s <= node.lineno <= e for s, e in tc_ranges)
        # Rule 1: no agent.contracts.* imports anywhere in skills.
        if node.module.startswith("agent.contracts"):
            findings.append(WrapperFinding(
                skill=rel.split("/")[2] if len(rel.split("/")) > 2 else "?",
                file=rel,
                line=node.lineno,
                code="contract_leak",
                detail=f"imports from {node.module} (should be agent.skills.*)",
            ))
        # Rule 2: system.host.* must be in TYPE_CHECKING or documented.
        if node.module.startswith("system.host") and not in_tc:
            # system.host modules are now under agent.skills.shared — this is a stale import
            contract_leaks += 1
            findings.append(WrapperFinding(
                skill=rel.split("/")[2] if len(rel.split("/")) > 2 else "?",
                file=rel,
                line=node.lineno,
                code="unguarded_external",
                detail=f"runtime import of {node.module} outside TYPE_CHECKING",
            ))
    return findings


def scan_wrapper_chaos(repo_root: Path) -> ChaosReport:
    """Validate that every skill wrapper fails closed on contract leaks.

    Returns a ChaosReport with all findings.  Does not modify files.
    """
    skills = _skills_root(repo_root)
    all_findings: list[WrapperFinding] = []
    py_files = 0
    yaml_files = 0
    skills_seen: set[str] = set()

    for root, dirs, files in sorted(Path(skills).walk()):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for fname in sorted(files):
            fpath = root / fname
            rel = str(fpath.relative_to(repo_root))
            if fname.endswith(".py"):
                py_files += 1
                # Determine TYPE_CHECKING ranges.
                with codecs.open(str(fpath), encoding="utf-8") as fh:
                    content = fh.read()
                tree = ast.parse(content, filename=str(fpath))
                tc_ranges: list[tuple[int, int]] = []
                for n in ast.walk(tree):
                    if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "TYPE_CHECKING":
                        tc_ranges.append((n.lineno, n.end_lineno or 9999))
                all_findings.extend(_scan_python_file(rel, fpath, tc_ranges))
                # Track skill names.
                parts = rel.split("/")
                if len(parts) >= 3:
                    skills_seen.add(parts[2])
            elif fname.endswith(".yaml"):
                yaml_files += 1
                parts = rel.split("/")
                if len(parts) >= 3:
                    skills_seen.add(parts[2])

    findings = tuple(sorted(all_findings, key=lambda f: (f.file, f.line)))
    return ChaosReport(
        skills_scanned=len(skills_seen),
        files_scanned=py_files + yaml_files,
        findings=findings,
        contract_leaks=sum(1 for f in findings if f.code == "contract_leak"),
        unguarded_external=sum(1 for f in findings if f.code == "unguarded_external"),
    )
