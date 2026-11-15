"""Planner stdin entrypoint: python -m agents.skills.planner < request.json"""

from __future__ import annotations

from agents.shared.io import error_response, ok_response, read_request, write_response


def main() -> int:
    try:
        request = read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    try:
        from agents.skills.planner.contracts.scanner import ScannerRunInput
        from agents.skills.planner.planning import scan

        scan_request = ScannerRunInput.model_validate(request.payload.get("scan", {}))
        result = scan(request.state_root, scan_request)
        write_response(ok_response(result.model_dump(mode="json")))
        return 0
    except Exception as exc:  # the process boundary is the error surface
        write_response(error_response("planner_failed", f"{type(exc).__name__}: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
