"""Auditor stdin entrypoint: python -m agents.skills.auditor < request.json"""

from __future__ import annotations

from agents.shared.io import error_response, ok_response, read_request, write_response
from agents.skills.auditor.auditing import run


def main() -> int:
    try:
        request = read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    try:
        payload = request.payload
        result = run(
            payload.get("workspace_root", request.workspace),
            request=str(payload.get("request", request.todo_id)),
            scope=str(payload.get("scope", ".")),
            capabilities=tuple(payload.get("capabilities", ())),
        )
        findings = [f.model_dump(mode="json") for f in getattr(result, "findings", ())]
        capabilities = list(getattr(result, "executed_capabilities", ()))
        write_response(ok_response({"findings": findings, "capabilities": capabilities}))
        return 0
    except Exception as exc:  # the process boundary is the error surface
        write_response(error_response("auditor_failed", f"{type(exc).__name__}: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
