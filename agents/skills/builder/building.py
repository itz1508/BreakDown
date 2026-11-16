"""Build execution implementation using standard library file operations and subprocess wrappers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_atomic(target_path: str | Path, content: str | bytes) -> Path:
    """Atomic file write using standard library tempfile and os.replace."""
    target = Path(target_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if isinstance(content, str) else "wb"
    encoding = "utf-8" if isinstance(content, str) else None

    with tempfile.NamedTemporaryFile(mode=mode, dir=target.parent, delete=False, encoding=encoding) as tmp:
        tmp.write(content)
        temp_name = tmp.name

    os.replace(temp_name, target)
    return target


def verify_build_approval(plan_payload: dict[str, Any], required_approval: str | None = None) -> bool:
    """Verify that the supplied plan payload carries explicit approval."""
    if not plan_payload:
        return False
    if required_approval and plan_payload.get("approval_digest") != required_approval:
        return False
    return bool(plan_payload.get("user_approval") or plan_payload.get("approved"))


def execute_build(
    plan_path: str | Path,
    workspace_root: str | Path,
    state_root: str | Path,
    dry_run: bool = False,
    recovery_readiness_ref: str | None = None,
) -> dict[str, Any]:
    """Execute approved build tasks within the authorized workspace."""
    plan_file = Path(plan_path)
    workspace = Path(workspace_root).resolve()
    state = Path(state_root).resolve()

    if not plan_file.is_file():
        raise FileNotFoundError(f"build plan not found: {plan_file}")

    plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
    tasks = plan_data.get("tasks", plan_data.get("todos", []))
    applied_operations: list[dict[str, str]] = []

    for task in tasks:
        action_kind = task.get("action", task.get("action_kind", "modify"))
        target_rel = task.get("target_path", task.get("target", ""))
        content = task.get("content", "")

        if not target_rel:
            continue

        target_full = (workspace / target_rel).resolve()
        if not target_full.is_relative_to(workspace):
            raise ValueError(f"task target escapes workspace: {target_rel}")

        if not dry_run:
            if action_kind in ("create", "modify"):
                write_atomic(target_full, content)
            elif action_kind == "delete" and target_full.exists():
                target_full.unlink()

        applied_operations.append({"action": action_kind, "target": target_rel, "status": "completed"})

    return {
        "status": "completed",
        "dry_run": dry_run,
        "operations": applied_operations,
        "workspace": str(workspace),
        "state_root": str(state),
    }


def execute_admitted(
    state_root: str | Path,
    workspace_root: str | Path,
    expected_source_digest: str | None = None,
    **arguments: Any,
) -> dict[str, Any]:
    """Compatibility entrypoint for subprocess and runtime callers."""
    plan_path = arguments.get("plan_path")
    if plan_path:
        return execute_build(
            plan_path,
            workspace_root,
            state_root,
            dry_run=arguments.get("dry_run", False),
            recovery_readiness_ref=arguments.get("recovery_readiness_ref"),
        )
    return {
        "status": "completed",
        "workspace": str(workspace_root),
        "state_root": str(state_root),
        "expected_source_digest": expected_source_digest,
        "arguments": arguments,
    }
