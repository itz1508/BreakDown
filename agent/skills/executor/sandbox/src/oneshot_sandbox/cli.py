"""Explicit standalone actions; never infer authorization from CLI or candidate data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contracts import SandboxExecutionRequest
from .integrations import backend_names, create_backend
from .recovery import AttemptStore
from .runner import StandaloneRunner, preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Standalone OneShot Sandbox")
    sub = parser.add_subparsers(dest="cmd", required=True)
    verify = sub.add_parser("validate", help="validate admission-bound bundle and snapshot without a remote provider")
    verify.add_argument("request", type=Path)
    execute = sub.add_parser("execute", help="execute against a selected registered backend and immutable image")
    execute.add_argument("request", type=Path)
    execute.add_argument("--backend", required=True, choices=backend_names(), help="selected trusted integration")
    execute.add_argument("--app", required=True, help="existing backend app/resource")
    execute.add_argument("--create-app", action="store_true", help="explicitly allow creating app if absent")
    execute.add_argument("--state", type=Path, default=Path(".state/attempts.sqlite"))
    execute.add_argument("--output", type=Path, default=Path(".outputs"))
    missing = sub.add_parser("unresolved", help="list unreconciled attempt metadata")
    missing.add_argument("--state", type=Path, default=Path(".state/attempts.sqlite"))
    inspect = sub.add_parser("inspect", help="read-only inspect an uncertain backend attempt")
    inspect.add_argument("operation_id")
    inspect.add_argument("attempt_id")
    inspect.add_argument("--backend", required=True, choices=backend_names())
    inspect.add_argument("--app", required=True)
    inspect.add_argument("--state", type=Path, default=Path(".state/attempts.sqlite"))
    args = parser.parse_args(argv)
    try:
        if args.cmd == "unresolved":
            for record in AttemptStore(args.state).unresolved():
                print(
                    json.dumps(
                        {
                            key: record[key]
                            for key in ("operation_id", "attempt_id", "state", "sandbox_name", "sandbox_id")
                        }
                    )
                )
            return 0
        if args.cmd == "inspect":
            backend = create_backend(args.backend, app_name=args.app)
            runner = StandaloneRunner(backend, AttemptStore(args.state), Path(".outputs"))
            print(json.dumps(runner.inspect_attempt(args.operation_id, args.attempt_id), indent=2))
            return 0
        req = SandboxExecutionRequest.model_validate_json(args.request.read_text(encoding="utf-8"))
        if args.cmd == "validate":
            preflight(req)
            print("VALID: offline source, candidate, policy and command-plan checks completed")
            return 0
        backend = create_backend(args.backend, app_name=args.app, create_app=args.create_app)
        result = StandaloneRunner(backend, AttemptStore(args.state), args.output).execute(req)
        print(result.model_dump_json(indent=2))
        return 0 if result.execution_status == "completed" and result.cleanup_state == "confirmed" else 1
    except Exception as exc:
        print(f"BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
