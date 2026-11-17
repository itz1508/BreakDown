"""Builder stdin entrypoint: python -m agents.skills.builder < request.json"""

from __future__ import annotations

from system import error_response, ok_response, read_request, write_response


def main() -> int:
    try:
        request = read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    try:
        from agents.skills.builder.building import execute_admitted

        result = execute_admitted(request.state_root, request.workspace, **request.payload)
        write_response(ok_response({"result": str(result)}))
        return 0
    except Exception as exc:  # the process boundary is the error surface
        write_response(error_response("builder_failed", f"{type(exc).__name__}: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
