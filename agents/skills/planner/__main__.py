"""Planner stdin entrypoint: python -m agents.skills.planner < request.json"""

from __future__ import annotations

from agents.shared.io import error_response, read_request, write_response


def main() -> int:
    try:
        read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    write_response(error_response("planner_pipeline_not_active", "planning produces no executable candidate yet"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
