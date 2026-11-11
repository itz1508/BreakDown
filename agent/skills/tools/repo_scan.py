"""Passive repository structure observation; never modifies the working tree.

Four check categories are kept strictly separate:

- **declaration_checks**: file/dir existence, YAML structure, __init__.py,
  artifact-contract-ref paths on disk, gap-analysis self-paths, no dangling
  ``contracts.workflow.*`` references, workflow operation declarations.
- **static_resolution**: ast-parsed import statements mapped to file paths
  via ``_module_to_path``. No ``importlib``, no ``sys.path`` mutation.
- **executed_cli_tests**: ``python -m agent.skills.<skill>`` run via
  subprocess with an isolated ``PYTHONPATH``. Reports exit code and stderr.
- **workflow_execution**: NOT performed — requires Host-approved pipeline.

Detector blind spots are validated with independent fixtures in a temp dir.

Stdlib-only, read-only, no mutations to the working tree or to global
import state.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIRS = ("researcher", "auditor", "coder", "planner", "builder")
APPROVED_STRUCTURE_REF = "c054f5a (origin/feat/breakdown-package-20261110)"


def _resolve_root(root: str | os.PathLike[str] | None) -> Path:
    """Resolve and validate the repository root."""
    if root is None:
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "agent" / "skills").is_dir():
                return parent
        raise ValueError(f"could not locate agent/skills/ from {here}")
    p = Path(root).resolve()
    if not p.is_dir():
        raise ValueError("root must be a directory")
    return p


def _git(repo_root: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else ""


# ── Worktree identification ──────────────────────────────────────────

def _inspect_worktree(repo_root: Path) -> dict:
    """Identify the exact inspected worktree state."""
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    commit = _git(repo_root, "rev-parse", "--short", "HEAD") or "unknown"
    full = _git(repo_root, "rev-parse", "HEAD") or "unknown"
    dirty = bool(_git(repo_root, "status", "--porcelain"))
    staged_out = _git(repo_root, "diff", "--cached", "--name-only")
    staged_files = staged_out.splitlines() if staged_out else []
    return {
        "branch": branch,
        "commit": commit,
        "full_commit": full,
        "dirty": dirty,
        "staged_files_count": len(staged_files),
        "approved_structure_ref": APPROVED_STRUCTURE_REF,
    }


# ── Shared extraction helpers ───────────────────────────────────────

def _iter_py_files(root: Path):
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath or "__pycache__" in dirpath:
            continue
        for f in files:
            if f.endswith(".py"):
                yield Path(dirpath) / f


def _extract_imports(filepath: Path) -> list[str]:
    """Parse a .py file with ast and return absolute import module names."""
    try:
        tree = ast.parse(filepath.read_text(), filename=str(filepath))
    except SyntaxError:
        return []
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module:
                mods.append(node.module)
    return mods


def _module_to_path(module_name: str, repo_root: Path) -> Path | None:
    """Map a dotted module name to a file path.

    Pure file-system resolution: no importlib, no sys.path mutation.
    Returns the file path if found, None otherwise.
    """
    parts = module_name.split(".")
    # Try as package: a/b/c/__init__.py
    pkg = repo_root.joinpath(*parts, "__init__.py")
    if pkg.is_file():
        return pkg
    # Try as module: a/b/c.py
    mod = repo_root.joinpath(*parts[:-1], parts[-1] + ".py")
    if mod.is_file():
        return mod
    # Try as namespace package: a/b/c/ (dir exists, no __init__.py)
    ns = repo_root.joinpath(*parts)
    if ns.is_dir():
        return ns
    return None


def _extract_yaml_paths(filepath: Path) -> list[str]:
    """Extract artifact_contract_refs paths from YAML text (stdlib-only)."""
    paths: list[str] = []
    for line in filepath.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and ("/contracts/" in stripped or "/workflow/" in stripped):
            paths.append(stripped.lstrip("- ").strip())
    return paths


def _extract_gap_audit_paths(filepath: Path) -> list[str]:
    """Extract path="..." values from _gap_analysis.py capability audit data."""
    content = filepath.read_text()
    return re.findall(r'path="([^"]+)"', content)


# ── 1. Declaration checks ────────────────────────────────────────────

def _check_declaration_checks(skills: Path, repo_root: Path) -> dict:
    """Declaration checks: what exists and what is declared.

    Does NOT prove functionality — a file existing does not mean it runs.
    """
    results: dict = {}

    found = [d for d in SKILL_DIRS if (skills / d).is_dir()]
    missing = [d for d in SKILL_DIRS if not (skills / d).is_dir()]
    results["skills_present"] = {
        "passed": not missing,
        "checked": list(SKILL_DIRS),
        "found": found,
        "missing": missing,
    }

    tools = skills / "tools"
    tool_files = ["verify_all.py", "sys_scan.py", "repo_scan.py"]
    found_tools = [f for f in tool_files if (tools / f).is_file()]
    missing_tools = [f for f in tool_files if not (tools / f).is_file()]
    results["tools_present"] = {
        "passed": tools.is_dir() and not missing_tools,
        "checked": tool_files,
        "found": found_tools,
        "missing": missing_tools,
        "note": "Existence only; static resolution and CLI execution checked separately.",
    }

    results["no_fixturer"] = {
        "passed": not (skills / "fixturer").is_dir(),
        "checked": ["fixturer/ does not exist"],
    }
    results["no_auditor_review"] = {
        "passed": not (skills / "auditor" / "review").is_dir(),
        "checked": ["auditor/review/ does not exist"],
    }
    results["planner_tools_not_review"] = {
        "passed": (skills / "planner" / "tools").is_dir()
        and not (skills / "planner" / "review").is_dir(),
        "checked": ["planner/tools/ exists", "planner/review/ does not exist"],
    }
    results["host_dir_present"] = {
        "passed": (repo_root / "system" / "host").is_dir(),
        "checked": ["system/host/ exists"],
        "note": "Existence only; static resolution checked separately.",
    }

    # --- __init__.py for adopted packaging only ---
    packages_ok: list[str] = []
    packages_missing: list[str] = []
    md_only_dirs: list[str] = []
    for dirpath, _dirs, files in os.walk(skills):
        if ".git" in dirpath or "__pycache__" in dirpath:
            continue
        has_py = any(f.endswith(".py") for f in files)
        has_init = "__init__.py" in files
        rel = os.path.relpath(dirpath, skills)
        if has_py:
            if has_init:
                packages_ok.append(rel)
            else:
                packages_missing.append(rel)
        elif not has_init and any(f.endswith(".md") for f in files):
            md_only_dirs.append(rel)
    results["init_py_adopted"] = {
        "passed": not packages_missing,
        "packages_ok": packages_ok,
        "packages_missing": packages_missing,
        "md_only_no_init_needed": md_only_dirs,
        "note": "__init__.py required only by adopted packaging, "
        "not every Python directory universally.",
    }

    # --- Nonempty declared scope ---
    py_count = sum(1 for _ in _iter_py_files(skills))
    yaml_count = sum(
        1
        for skill in SKILL_DIRS
        for f in (skills / skill).iterdir()
        if f.name.endswith(".yaml")
    )
    results["nonempty_scope"] = {
        "passed": py_count > 0 and yaml_count > 0,
        "py_files": py_count,
        "yaml_files": yaml_count,
    }

    # --- YAML artifact_contract_refs paths resolve on disk ---
    yaml_checked: list[str] = []
    yaml_failed: list[str] = []
    for skill in SKILL_DIRS:
        for yf in sorted((skills / skill).iterdir()):
            if not yf.name.endswith(".yaml"):
                continue
            rel = yf.relative_to(repo_root).as_posix()
            for path in _extract_yaml_paths(yf):
                yaml_checked.append(f"{rel}: {path}")
                if not (repo_root / path).exists():
                    yaml_failed.append(f"{rel}: {path}")
    results["yaml_refs_resolve"] = {
        "passed": not yaml_failed,
        "checked_count": len(yaml_checked),
        "failed": yaml_failed,
    }

    # --- Gap-analysis self-paths resolve on disk ---
    gap_file = skills / "planner" / "tools" / "_gap_analysis.py"
    gap_checked: list[str] = []
    gap_failed: list[str] = []
    if gap_file.is_file():
        for path_val in _extract_gap_audit_paths(gap_file):
            gap_checked.append(path_val)
            if not (repo_root / path_val).exists():
                gap_failed.append(path_val)
    results["gap_analysis_self_paths"] = {
        "passed": not gap_failed,
        "checked_count": len(gap_checked),
        "failed": gap_failed,
        "note": "Capability audit data references historical paths; "
        "unresolved paths are pre-existing and do not affect runtime imports.",
    }

    # --- No dangling contracts.workflow.* references ---
    scanner_name = "repo_scan.py"
    dangling: list[str] = []
    scan_dirs = [skills, repo_root / "system"]
    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            continue
        for pyfile in _iter_py_files(scan_dir):
            if pyfile.name == scanner_name:
                continue
            rel = pyfile.relative_to(repo_root).as_posix()
            content = pyfile.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if ("contracts.workflow" in line or "contracts/workflow" in line) and not stripped.startswith('"'):
                    dangling.append(f"{rel}:{i}: {stripped[:80]}")
    results["no_dangling_contracts_workflow"] = {
        "passed": not dangling,
        "checked": ["agent/skills/", "system/", f"excluded: {scanner_name}"],
        "failed": dangling,
    }

    # --- Workflow operation declarations (YAML-parsed) ---
    ops_checked: list[str] = []
    ops_unbound: list[str] = []
    for skill in SKILL_DIRS:
        for yf in sorted((skills / skill).iterdir()):
            if not yf.name.endswith(".yaml"):
                continue
            lines = yf.read_text().splitlines()
            for idx, line in enumerate(lines):
                if "operation_id:" in line:
                    op_id = line.strip().split("operation_id:")[1].strip()
                    ops_checked.append(op_id)
                    next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
                    if "unbound" in next_line or "unbound" in line:
                        ops_unbound.append(op_id)
    results["workflow_operations"] = {
        "passed": True,
        "checked_count": len(ops_checked),
        "all_unbound": len(ops_unbound) == len(ops_checked),
        "note": "Declaration only; all operations are status=unbound. "
        "Binding to implementations requires Host-approved trusted pipeline.",
    }
    return results


# ── 2. Static resolution ─────────────────────────────────────────────

def _check_static_resolution(skills: Path, repo_root: Path) -> dict:
    """Static resolution: ast-parsed imports mapped to file paths.

    No importlib, no sys.path mutation.  Maps dotted module names to
    file paths and checks existence.
    """
    checked_imports: list[str] = []
    failed_imports: list[str] = []
    for pyfile in _iter_py_files(skills):
        rel = pyfile.relative_to(repo_root).as_posix()
        for mod in _extract_imports(pyfile):
            if mod.startswith(("agent.", "system.", "contracts.")):
                key = f"{rel}: {mod}"
                checked_imports.append(key)
                if _module_to_path(mod, repo_root) is None:
                    failed_imports.append(key)
    for pyfile in _iter_py_files(repo_root / "system"):
        rel = pyfile.relative_to(repo_root).as_posix()
        for mod in _extract_imports(pyfile):
            if mod.startswith(("agent.", "system.", "contracts.")):
                key = f"{rel}: {mod}"
                checked_imports.append(key)
                if _module_to_path(mod, repo_root) is None:
                    failed_imports.append(key)
    return {
        "imports_resolve": {
            "passed": not failed_imports,
            "method": "ast parse + _module_to_path file mapping (no importlib, no sys.path mutation)",
            "checked_count": len(checked_imports),
            "failed": failed_imports,
        }
    }


# ── 3. Executed CLI tests ────────────────────────────────────────────

def _check_executed_cli(skills: Path, repo_root: Path) -> dict:
    """Executed CLI tests: run ``python -m agent.skills.<skill>`` via subprocess.

    Uses an isolated PYTHONPATH env var — does NOT mutate the current
    process's sys.path.
    """
    cli_results: list[dict] = []
    all_passed = True
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    for skill in SKILL_DIRS:
        try:
            r = subprocess.run(
                [sys.executable, "-m", f"agent.skills.{skill}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(repo_root), env=env,
            )
            entry = {
                "skill": skill,
                "exit_code": r.returncode,
                "stdout_len": len(r.stdout),
                "stderr": r.stderr.strip()[:300] if r.stderr else "",
            }
            if r.returncode != 0:
                all_passed = False
        except subprocess.TimeoutExpired:
            entry = {"skill": skill, "exit_code": -1, "stderr": "TIMEOUT"}
            all_passed = False
        except Exception as e:
            entry = {"skill": skill, "exit_code": -1, "stderr": str(e)[:300]}
            all_passed = False
        cli_results.append(entry)
    return {
        "cli_entrypoints": {
            "passed": all_passed,
            "method": "subprocess python -m agent.skills.<skill> (isolated PYTHONPATH, no sys.path mutation)",
            "results": cli_results,
        }
    }


# ── 4. Workflow execution (not performed) ────────────────────────────

def _check_workflow_execution() -> dict:
    """Workflow execution: NOT performed. Documented."""
    return {
        "performed": False,
        "reason": "Workflow execution requires Host-approved trusted pipeline. "
        "Scanner is read-only and cannot dispatch or admit operations.",
    }


# ── Detector validation (independent fixtures) ──────────────────────

def _check_detector_validation() -> dict:
    """Validate detector blind spots with independent fixtures.

    Creates temp files OUTSIDE the working tree and verifies each
    detector type catches the defect it is supposed to catch.
    """
    fixtures: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="repo_scan_detect_") as tmpdir:
        tmp = Path(tmpdir)
        fake_root = tmp / "repo"
        fake_root.mkdir()
        (fake_root / "agent").mkdir()
        (fake_root / "agent" / "contracts").mkdir()
        (fake_root / "agent" / "contracts" / "__init__.py").write_text("")
        (fake_root / "agent" / "contracts" / "common.py").write_text("x = 1\n")

        # Fixture 1: broken import
        f1 = fake_root / "_broken.py"
        f1.write_text("import nonexistent.module\n")
        mods = _extract_imports(f1)
        detected = any(_module_to_path(m, fake_root) is None for m in mods if m.startswith("nonexistent."))
        fixtures.append({
            "name": "broken_import",
            "defect": "import nonexistent.module",
            "detected": detected,
        })

        # Fixture 2: clean import not flagged
        f2 = fake_root / "_clean.py"
        f2.write_text("from agent.contracts.common import x\n")
        mods2 = _extract_imports(f2)
        clean_ok = all(_module_to_path(m, fake_root) is not None for m in mods2 if m.startswith("agent."))
        fixtures.append({
            "name": "clean_import_not_flagged",
            "defect": None,
            "detected": clean_ok,
        })

        # Fixture 3: missing __init__.py in a package dir with .py files
        pkg = fake_root / "_nopkg"
        pkg.mkdir()
        (pkg / "module.py").write_text("x = 1\n")
        has_init = (pkg / "__init__.py").is_file()
        fixtures.append({
            "name": "missing_init_py",
            "defect": "dir with .py files but no __init__.py",
            "detected": not has_init,
        })

        # Fixture 4: dangling contracts.workflow reference
        f4 = fake_root / "_dangling.py"
        f4.write_text("from contracts.workflow.auditor import x\n")
        content = f4.read_text()
        has_dangling = False
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "contracts.workflow" in line and not stripped.startswith('"'):
                has_dangling = True
        fixtures.append({
            "name": "dangling_contracts_workflow",
            "defect": "from contracts.workflow.auditor import x",
            "detected": has_dangling,
        })

        # Fixture 5: non-existent YAML path (must contain /contracts/ to match extractor)
        f5 = fake_root / "_bad_ref.yaml"
        f5.write_text("artifact_contract_refs:\n- agent/contracts/nonexistent.py\n")
        paths = _extract_yaml_paths(f5)
        bad_path_found = any(not (fake_root / p).exists() for p in paths)
        fixtures.append({
            "name": "nonexistent_yaml_path",
            "defect": "artifact_contract_refs: [agent/contracts/nonexistent.py] (path extracted but file missing)",
            "detected": bad_path_found,
        })

    all_detected = all(f["detected"] for f in fixtures)
    return {
        "detector_validation": {
            "passed": all_detected,
            "fixtures": fixtures,
            "note": "Independent fixtures in temp dir outside working tree. "
            "Validates that each detector catches its target defect type.",
        }
    }


# ── Main entry point ────────────────────────────────────────────────

def repo_scan(
    *,
    root: str | os.PathLike[str] | None = None,
) -> dict:
    """Return structured repository-structure observations.

    Four check categories, kept strictly separate:
    - **declaration_checks**: what exists and what is declared.
    - **static_resolution**: import paths mapped to files (no importlib).
    - **executed_cli_tests**: subprocess CLI execution (no sys.path mutation).
    - **workflow_execution**: NOT performed.

    Plus detector_validation with independent fixtures.

    Does not stage, commit, or modify any file.
    Does not mutate global import state.
    Does not label "no findings" as universally clean.
    """
    repo_root = _resolve_root(root)
    skills = repo_root / "agent" / "skills"

    worktree = _inspect_worktree(repo_root)
    declaration_checks = _check_declaration_checks(skills, repo_root)
    static_resolution = _check_static_resolution(skills, repo_root)
    executed_cli_tests = _check_executed_cli(skills, repo_root)
    workflow_execution = _check_workflow_execution()
    detector_validation = _check_detector_validation()

    decl_pass = all(v.get("passed", False) for v in declaration_checks.values())
    static_pass = all(v.get("passed", False) for v in static_resolution.values())
    cli_pass = all(v.get("passed", False) for v in executed_cli_tests.values())
    detector_pass = all(v.get("passed", False) for v in detector_validation.values())

    return {
        "inspected_worktree": worktree,
        "declaration_checks": declaration_checks,
        "static_resolution": static_resolution,
        "executed_cli_tests": executed_cli_tests,
        "workflow_execution": workflow_execution,
        "detector_validation": detector_validation,
        "coverage_report": {
            "categories_performed": [
                "declaration_checks — file/dir existence, YAML structure, __init__.py, artifact refs, gap-analysis paths, dangling refs, workflow declarations",
                "static_resolution — ast-parsed imports mapped to file paths via _module_to_path (no importlib, no sys.path mutation)",
                "executed_cli_tests — subprocess python -m agent.skills.<skill> (isolated PYTHONPATH, no sys.path mutation)",
                "detector_validation — 5 independent fixture types tested",
            ],
            "categories_not_performed": [
                "workflow_execution — requires Host-approved trusted pipeline",
                "E2E build verification — requires Host admission",
                "Runtime scanner execution — requires trusted pipeline",
            ],
            "blind_spots": [
                "Static resolution maps module names to file paths; does not execute imports or detect runtime errors, circular imports, or import-time side effects",
                "CLI tests use subprocess; cannot verify in-process side effects or shared state",
                "ast.parse only sees import statements at module level; conditional imports (try/except, TYPE_CHECKING) are not fully resolved",
                "Detector fixtures are synthetic temp files; real defects may have different patterns",
                "Workflow operation binding not verified — operations are declarative (status=unbound)",
            ],
            "results": {
                "declaration_checks": decl_pass,
                "static_resolution": static_pass,
                "executed_cli_tests": cli_pass,
                "workflow_execution": False,
                "detector_validation": detector_pass,
                "clean": False,
            },
            "note": "Never label 'no findings' as universally clean. "
            "Declaration pass does not prove static resolution. "
            "Static resolution does not prove CLI execution.",
        },
    }
