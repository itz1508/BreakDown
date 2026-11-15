"""OneShot CLI — thin host entrypoint using cmd.Cmd for dispatch.

Supports both one-shot (``python -m agent audit --scope agent/``)
and interactive (``python -m agent``) modes via ``cmd.Cmd``.
"""

from __future__ import annotations

import cmd as cmdmod
import json
import shlex
import sys
from pathlib import Path


def _cmd_doctor(state_root: str = "/tmp/oneshot-state") -> int:
    """Run environment diagnostics."""
    print("OneShot Doctor")
    print("=" * 40)

    import pydantic

    print(f"Pydantic version: {pydantic.__version__}")

    import rfc8785

    print(f"RFC 8785 library: rfc8785 {getattr(rfc8785, '__version__', 'unknown')}")

    import yaml

    print(f"PyYAML version: {yaml.__version__}")

    # Check provider SDKs
    try:
        import openai

        print(f"OpenAI SDK: {openai.__version__} (meta extra available)")
    except ImportError:
        print("OpenAI SDK: not installed (meta extra not available)")

    # Check state root
    sr = Path(state_root)
    if sr.exists():
        print(f"State root: {sr} (exists)")
    else:
        print(f"State root: {sr} (not created yet)")

    # Check scanner capabilities
    from agent.runtime.controller import HostController

    controller = HostController(state_root)
    print(f"Scanner capabilities: {controller.scanner.supported_capabilities or 'none registered'}")
    print(f"Providers: {controller.providers.registered_providers}")

    print("\nDoctor: OK")
    return 0


def _cmd_run(task_id: str, state_root: str = "/tmp/oneshot-state") -> int:
    """Execute an existing Research task through the registered host, never simulate completion."""
    from agent.runtime.controller import Stage

    from agent.skills.researcher.researching import execute_research
    from app.service import MVPError, MVPService

    service = MVPService(state_root)
    state = service.host.get_state(task_id)
    if state is None:
        print(f"Task {task_id}: not found; submit a task with an input artifact first", file=sys.stderr)
        return 1
    if state.current_stage is not Stage.RESEARCH:
        print(
            f"Task {task_id}: no executable runner registered for stage {state.current_stage.value}",
            file=sys.stderr,
        )
        return 1
    try:
        outcome = execute_research(service, task_id)
    except (MVPError, ValueError) as exc:
        print(f"Task {task_id}: Research blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(outcome, sort_keys=True))
    return 0


def _cmd_scan(task_id: str, request_file: str, state_root: str = "/tmp/oneshot-state") -> int:
    """Run the API's exact host scanner and print persisted events as JSON lines."""
    from pydantic import ValidationError

    from agent.contracts.scanner import ScannerOutcome, ScannerRunInput
    from agent.runtime.controller import TransitionError

    from app.service import MVPError, MVPService

    try:
        request = ScannerRunInput.model_validate_json(Path(request_file).read_bytes())
    except (OSError, ValidationError) as exc:
        print(f"Invalid scanner request file: {type(exc).__name__}", file=sys.stderr)
        return 1

    def show(event: dict[str, object]) -> None:
        print(json.dumps(event, sort_keys=True), flush=True)

    try:
        result = MVPService(state_root).scan_candidate(task_id, request, on_event=show)
    except (MVPError, TransitionError) as exc:
        print(f"Scanner blocked: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"type": "scanner_result", "result": result.model_dump(mode="json")}, sort_keys=True))
    return 0 if result.outcome is ScannerOutcome.PASS else 2


def _cmd_status(task_id: str, state_root: str = "/tmp/oneshot-state") -> int:
    """Show task status."""
    from agent.runtime.controller import HostController

    controller = HostController(state_root)
    state = controller.get_state(task_id)
    if state is None:
        print(f"Task {task_id}: not found")
        return 1
    print(json.dumps(state.model_dump(mode="json"), indent=2))
    return 0


def _cmd_resume(task_id: str, state_root: str = "/tmp/oneshot-state") -> int:
    """Resume a task from its last checkpoint."""
    from agent.runtime.controller import HostController

    controller = HostController(state_root)
    state = controller.get_state(task_id)
    if state is None:
        print(f"Task {task_id}: no checkpoint found")
        return 1
    print(f"Task {task_id} resumed at stage: {state.current_stage}")
    print(f"Completed stages: {state.completed_stages}")
    return 0


def _cmd_verify(task_id: str, state_root: str = "/tmp/oneshot-state") -> int:
    """Verify task completion."""
    from agent.runtime.controller import HostController, Stage

    controller = HostController(state_root)
    state = controller.get_state(task_id)
    if state is None:
        print(f"Task {task_id}: not found")
        return 1
    if state.current_stage == Stage.BUILD_VALIDATION and Stage.BUILD_VALIDATION in state.completed_stages:
        print(f"Task {task_id}: COMPLETED")
        return 0
    print(f"Task {task_id}: in progress (stage: {state.current_stage})")
    return 1


def _cmd_audit(args_str: str = "") -> int:
    """Read-only capability audit (static observations only)."""
    import argparse

    from agent.audit.core import CAPABILITY_ORDER, scan

    parser = argparse.ArgumentParser(
        prog="audit",
        description="Read-only OneShot capability audit (static observations only)",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Authorized repository root")
    parser.add_argument("--scope", default=".", help="Relative in-repository directory")
    parser.add_argument("--request", default="", help="User audit question, preserved without granting access")
    parser.add_argument(
        "--capability",
        action="append",
        choices=CAPABILITY_ORDER,
        default=[],
    )
    argv = shlex.split(args_str) if args_str else None
    args = parser.parse_args(argv)
    try:
        result = scan(args.root, args.scope, tuple(args.capability), request=args.request)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 2 if result.disposition == "blocked" else 0


class OneShotShell(cmdmod.Cmd):
    """Interactive and one-shot command dispatcher using cmd.Cmd."""

    intro = "OneShot Agent. Type help or ? to list commands."
    prompt = "(oneshot) "
    ruler = "="

    def do_doctor(self, arg: str) -> bool:
        """Run environment diagnostics."""
        return _cmd_doctor() == 0 and False or True

    def do_audit(self, arg: str) -> bool:
        """Read-only capability audit (static observations only)."""
        _cmd_audit(arg)
        return False

    def do_run(self, arg: str) -> bool:
        """Execute an existing Research task: run <task_id>"""
        parts = shlex.split(arg) if arg else []
        if not parts:
            print("Usage: run <task_id>")
            return False
        _cmd_run(parts[0])
        return False

    def do_scan(self, arg: str) -> bool:
        """Run host scanner: scan <task_id> <request.json> [--state-root PATH]"""
        parts = shlex.split(arg) if arg else []
        if len(parts) < 2:
            print("Usage: scan <task_id> <request_file> [--state-root PATH]")
            return False
        state_root = "/tmp/oneshot-state"
        if "--state-root" in parts:
            idx = parts.index("--state-root")
            state_root = parts[idx + 1] if idx + 1 < len(parts) else state_root
        _cmd_scan(parts[0], parts[1], state_root)
        return False

    def do_status(self, arg: str) -> bool:
        """Show task status: status <task_id>"""
        parts = shlex.split(arg) if arg else []
        if not parts:
            print("Usage: status <task_id>")
            return False
        _cmd_status(parts[0])
        return False

    def do_resume(self, arg: str) -> bool:
        """Resume a task: resume <task_id>"""
        parts = shlex.split(arg) if arg else []
        if not parts:
            print("Usage: resume <task_id>")
            return False
        _cmd_resume(parts[0])
        return False

    def do_verify(self, arg: str) -> bool:
        """Verify task completion: verify <task_id>"""
        parts = shlex.split(arg) if arg else []
        if not parts:
            print("Usage: verify <task_id>")
            return False
        _cmd_verify(parts[0])
        return False

    def do_exit(self, arg: str) -> bool:
        """Exit the shell."""
        return True

    do_EOF = do_exit
    do_quit = do_exit


def main() -> int:
    """Main CLI entrypoint — one-shot if args given, interactive otherwise."""
    if len(sys.argv) < 2:
        OneShotShell().cmdloop()
        return 0

    shell = OneShotShell()
    line = " ".join(sys.argv[1:])
    shell.onecmd(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
